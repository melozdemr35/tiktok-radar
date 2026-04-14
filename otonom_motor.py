import google.generativeai as genai
import json
import os
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    
    # --- 1. ADIM: TİKTOK'TAN TAZE VERİ ÇEK ---
    print("TikTok Keşfet'e sızılıyor...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # TikTok Keşfet sayfası
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle")
            page.wait_for_timeout(8000) # Sayfanın yüklenmesi için süre
            
            # Sayfadaki video açıklamalarını topla
            # TikTok'un güncel seçicilerini (selector) hedefliyoruz
            descriptions = page.query_selector_all('div[data-e2e="explore-item-desc"]')
            
            for desc in descriptions[:10]: # En taze 10 videoyu al
                text = desc.inner_text()
                if text:
                    yeni_videolar.append({"desc": text, "hashtagler": "Keşfetten Yeni"})
            
            browser.close()
            print(f"{len(yeni_videolar)} adet yeni video yakalandı!")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

    # --- 2. ADIM: VERİTABANINI GÜNCELLE ---
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, "trend_veritabani.json")
    
    with open(db_path, "r", encoding="utf-8") as f:
        eski_veriler = json.load(f)
    
    # Yeni videoları listenin en başına ekle (Tazeler üstte kalsın)
    guncel_liste = yeni_videolar + eski_veriler
    # Listenin çok şişmemesi için son 3000 videoda sabitleyelim
    guncel_liste = guncel_liste[:3000] 
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(guncel_liste, f, ensure_ascii=False, indent=4)

    # --- 3. ADIM: GEMINI İLE TAZE ANALİZ YAP ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Gemini'ye özellikle en yeni verileri vurguluyoruz
    analiz_verisi = str(yeni_videolar) if yeni_videolar else str(eski_veriler[:10])
    prompt = f"Şu an TikTok Keşfet'te taze yakaladığım videolar şunlar: {analiz_verisi}. Bu trendlere göre Melih için 3 içerik fikri üret."
    
    try:
        response = model.generate_content(prompt)
        with open(os.path.join(base_path, "son_analiz.txt"), "w", encoding="utf-8") as f:
            f.write(response.text)
        print("İşlem başarıyla tamamlandı!")
    except Exception as e:
        print(f"Analiz hatası: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        veri_yakala_ve_analiz_et(api_key)
    else:
        print("Hata: API Key yok!")
