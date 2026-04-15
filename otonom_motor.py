import google.generativeai as genai
import json
import os
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    
    # --- 1. ADIM: TİKTOK'TAN TAZE VERİ ÇEK ---
    print("TikTok Keşfet'e 'Görünmezlik Modu' ile sızılıyor...")
    try:
        with sync_playwright() as p:
            # TikTok'un bot olduğunu anlamaması için gerçek bir tarayıcı kimliği tanımlıyoruz
            browser = p.chromium.launch(headless=True)
            
            # KRİTİK EKLEME: Gerçek kullanıcı kimliği (User-Agent)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            # TikTok Keşfet sayfası
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=60000)
            
            # --- TURBO KAYDIRMA VE BEKLEME ---
            print("Sayfa derinlemesine taranıyor... (Beklemeli Mod)")
            for i in range(12): 
                page.mouse.wheel(0, 4000)
                # TikTok şüphelenmesin diye rastgele küçük beklemeler
                page.wait_for_timeout(2000) 
                if i % 3 == 0:
                    print(f"Tarama ilerlemesi: %{int((i/12)*100)}")
            
            # Tüm video kartlarını yakala
            items = page.query_selector_all('div[data-e2e="explore-item"]')
            
            if len(items) == 0:
                print("⚠️ UYARI: TikTok video listesini boş döndürdü. Muhtemelen bot kontrolüne takıldık.")
            
            for item in items[:300]:
                try:
                    desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]')
                    desc_text = desc_elem.inner_text() if desc_elem else ""
                    
                    music_elem = item.query_selector('h4[data-e2e="explore-item-music"]')
                    music_text = music_elem.inner_text() if music_elem else "Popüler Akım"
                    
                    if desc_text or music_text:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text,
                            "hashtagler": "Keşfetten Yeni"
                        })
                except:
                    continue
            
            browser.close()
            print(f"Bitti! Toplam {len(yeni_videolar)} adet taze veri yakalandı.")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

    # --- 2. ADIM: VERİTABANINI GÜNCELLE ---
    db_path = "trend_veritabani.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []
    
    # Sadece yeni video varsa dosya yazma işlemini yap (Boş veriyle dosyayı bozma)
    if len(yeni_videolar) > 0:
        guncel_liste = yeni_videolar + eski_veriler
        guncel_liste = guncel_liste[:10000] 
        
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(guncel_liste, f, ensure_ascii=False, indent=4)
        print(f"Veritabanı başarıyla güncellendi. Mevcut toplam video: {len(guncel_liste)}")
    else:
        print("❌ Yeni veri yakalanamadığı için veritabanı dosyası güncellenmedi.")

    # --- 3. ADIM: GEMINI İLE TAZE ANALİZ YAP ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    analiz_verisi = str(yeni_videolar[:30]) if yeni_videolar else str(eski_veriler[:30])
    
    prompt = f"""
    Aşağıdaki güncel TikTok verilerini analiz et: {analiz_verisi}. 
    Bu verilere dayanarak, içerik üreticileri için uygulanabilir 5 benzersiz trend stratejisi oluştur.
    Lütfen her madde için akımın ne olduğunu ve nasıl uygulanması gerektiğini profesyonelce açıkla.
    Sadece strateji maddelerini yaz; isim, hitap, giriş veya kapanış cümlesi kurma.
    """
    
    try:
        response = model.generate_content(prompt)
        current_dir = os.getcwd()
        output_file = os.path.join(current_dir, "son_analiz.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"Analiz raporu güncellendi.")
    except Exception as e:
        print(f"Analiz hatası: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        veri_yakala_ve_analiz_et(api_key)
    else:
        print("Hata: API Key bulunamadı!")
