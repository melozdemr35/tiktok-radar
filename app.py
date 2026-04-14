import google.generativeai as genai
import json
import os
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    
    # --- 1. ADIM: TİKTOK'TAN AGRESİF VERİ ÇEK ---
    print("TikTok Derin Tarama Başlatıldı... (Turbo Mod)")
    try:
        with sync_playwright() as p:
            # Robotu hızlandırmak için gereksiz kaynakları yüklemiyoruz
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # TikTok Keşfet
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=60000)
            
            # --- TURBO KAYDIRMA MOTORU ---
            # 1000 video hedefine yaklaşmak için sayfayı daha hızlı ve derin kaydırıyoruz
            print("Sayfa derinlemesine taranıyor, veriler toplanıyor...")
            for i in range(12):  # Kaydırma sayısını artırdık
                page.mouse.wheel(0, 5000)  # Her seferinde dev adımlarla aşağı atla
                page.wait_for_timeout(1500) # Verilerin yüklenmesi için kısa bir es ver
                if i % 3 == 0:
                    print(f"Tarama aşaması: %{int((i/12)*100)}")
            
            # Keşfet yazılarını topla
            descriptions = page.query_selector_all('div[data-e2e="explore-item-desc"]')
            
            # İlk 300 videoyu hedefe koyuyoruz (Ban riskine karşı en hızlı ve güvenli sınır)
            for desc in descriptions[:300]:
                text = desc.inner_text()
                if text:
                    yeni_videolar.append({"desc": text, "hashtagler": "Trend Radarı"})
            
            browser.close()
            print(f"Mükemmel! {len(yeni_videolar)} adet taze veri sisteme işlenmeye hazır.")
    except Exception as e:
        print(f"Veri çekme sırasında bir aksama oldu: {e}")

    # --- 2. ADIM: VERİTABANINI GÜNCELLE ---
    db_path = "trend_veritabani.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []
    
    # Yeni videoları ekle ve kapasiteyi 10.000 yapalım ki veritabanı "devleşsin"
    guncel_liste = yeni_videolar + eski_veriler
    guncel_liste = guncel_liste[:10000] 
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(guncel_liste, f, ensure_ascii=False, indent=4)

    # --- 3. ADIM: PROFESYONEL ANALİZ RAPORU ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # En taze 30 veriyi analiz için gönderiyoruz
    analiz_verisi = str(yeni_videolar[:30]) if yeni_videolar else str(eski_veriler[:30])
    
    prompt = f"""
    Aşağıdaki güncel TikTok trend verilerini analiz et: {analiz_verisi}. 
    Bu verilere dayanarak, içerik üreticileri için uygulanabilir 5 adet benzersiz ve profesyonel içerik stratejisi oluştur.
    Her madde için:
    - Akımın temel mantığını açıkla.
    - Teknik olarak nasıl uygulanması gerektiğini anlat.
    - Hangi görsel estetiğin kullanılacağını belirt.
    
    NOT: Sadece strateji maddelerini yaz. İsim, hitap, giriş veya kapanış cümlesi kullanma. Profesyonel bir rapor dili kullan.
    """
    
    try:
        response = model.generate_content(prompt)
        
        # DOSYA YAZMA GARANTİSİ (Hafıza temizliği için her seferinde sıfırdan yazar)
        current_dir = os.getcwd()
        output_file = os.path.join(current_dir, "son_analiz.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print("Analiz raporu 'son_analiz.txt' dosyasına başarıyla basıldı!")
    except Exception as e:
        print(f"Gemini raporu yazarken bir hata aldı: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        veri_yakala_ve_analiz_et(api_key)
    else:
        print("Hata: GEMINI_API_KEY eksik!")
