import google.generativeai as genai
import json
import os
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    
    # --- 1. ADIM: TİKTOK'TAN TAZE VERİ ÇEK ---
    print("TikTok Keşfet'e sızılıyor... (Müzik Odaklı Tarama)")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # TikTok Keşfet sayfası
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=60000)
            
            # --- TURBO KAYDIRMA: Sayı artsın diye 12 kez kaydırıyoruz ---
            print("Sayfa derinlemesine taranıyor, video ve müzikler toplanıyor...")
            for i in range(12): 
                page.mouse.wheel(0, 4000)
                page.wait_for_timeout(1500)
                if i % 3 == 0:
                    print(f"Tarama ilerlemesi: %{int((i/12)*100)}")
            
            # Tüm video kartlarını yakala
            items = page.query_selector_all('div[data-e2e="explore-item"]')
            
            # --- ÜST SINIRI 300'E ÇIKARDIK (Sayı fırlasın diye) ---
            for item in items[:300]:
                try:
                    # Açıklama Metni
                    desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]')
                    desc_text = desc_elem.inner_text() if desc_elem else ""
                    
                    # GERÇEK ŞARKI İSMİ (İstediğin yer burası)
                    music_elem = item.query_selector('h4[data-e2e="explore-item-music"]')
                    music_text = music_elem.inner_text() if music_elem else "Popüler Akım"
                    
                    if desc_text or music_text:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text, # Şarkı ismi artık veritabanında!
                            "hashtagler": "Keşfetten Yeni"
                        })
                except:
                    continue
            
            browser.close()
            print(f"Mükemmel! {len(yeni_videolar)} adet taze veri yakalandı.")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

    # --- 2. ADIM: VERİTABANINI GÜNCELLE ---
    db_path = "trend_veritabani.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []
    
    # Yeni videoları eskilere ekle ve kapasiteyi 10.000 yaptık (Dev Veritabanı)
    guncel_liste = yeni_videolar + eski_veriler
    guncel_liste = guncel_liste[:10000] 
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(guncel_liste, f, ensure_ascii=False, indent=4)
    print("Veritabanı başarıyla şişirildi ve kaydedildi.")

    # --- 3. ADIM: GEMINI İLE TAZE ANALİZ YAP ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Analiz için en taze 30 veriyi gönderiyoruz
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
