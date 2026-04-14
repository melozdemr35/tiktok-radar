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
            page.wait_for_timeout(8000) 
            
            # TikTok'un keşfet yazılarını yakalayalım
            descriptions = page.query_selector_all('div[data-e2e="explore-item-desc"]')
            
            for desc in descriptions[:10]:
                text = desc.inner_text()
                if text:
                    yeni_videolar.append({"desc": text, "hashtagler": "Keşfetten Yeni"})
            
            browser.close()
            print(f"{len(yeni_videolar)} adet yeni video yakalandı!")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

    # --- 2. ADIM: VERİTABANINI GÜNCELLE ---
    # Dosya yollarını doğrudan ana dizin olarak belirliyoruz
    db_path = "trend_veritabani.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []
    
    # Yeni videoları ekle ve sabitle
    guncel_liste = yeni_videolar + eski_veriler
    guncel_liste = guncel_liste[:3000] 
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(guncel_liste, f, ensure_ascii=False, indent=4)

    # --- 3. ADIM: GEMINI İLE TAZE ANALİZ YAP ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    analiz_verisi = str(yeni_videolar) if yeni_videolar else str(eski_veriler[:10])
    prompt = f"Sen bir sosyal medya stratejistisin. Şu an Türkiye TikTok Keşfet'teki videolar şunlar: {analiz_verisi}. Melih için 3 etkili içerik fikri üret."
    
    try:
        response = model.generate_content(prompt)
        # Dosyayı doğrudan ana dizine yazdırıyoruz
        with open("son_analiz.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Analiz son_analiz.txt dosyasına başarıyla yazıldı!")
    except Exception as e:
        print(f"Analiz hatası: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        veri_yakala_ve_analiz_et(api_key)
    else:
        print("Hata: API Key bulunamadı!")
