import google.generativeai as genai
import json
import os
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    
    # --- 1. ADIM: TİKTOK'TAN TAZE VERİ ÇEK --- (Aynen Korundu)
    print("TikTok Keşfet'e sızılıyor...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle")
            page.wait_for_timeout(8000) 
            
            descriptions = page.query_selector_all('div[data-e2e="explore-item-desc"]')
            
            for desc in descriptions[:10]:
                text = desc.inner_text()
                if text:
                    yeni_videolar.append({"desc": text, "hashtagler": "Keşfetten Yeni"})
            
            browser.close()
            print(f"{len(yeni_videolar)} adet yeni video yakalandı!")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

    # --- 2. ADIM: VERİTABANINI GÜNCELLE --- (Aynen Korundu)
    db_path = "trend_veritabani.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []
    
    guncel_liste = yeni_videolar + eski_veriler
    guncel_liste = guncel_liste[:3000] 
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(guncel_liste, f, ensure_ascii=False, indent=4)

    # --- 3. ADIM: GEMINI İLE TAZE ANALİZ YAP --- (Profesyonelleştirildi)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    analiz_verisi = str(yeni_videolar) if yeni_videolar else str(eski_veriler[:10])
    
    # Prompt senin istediğin gibi; isim kullanmadan ve nasıl yapılacağını anlatan profesyonel moda çekildi
    prompt = f"""
    Aşağıdaki güncel TikTok verilerini analiz et: {analiz_verisi}. 
    Bu verilere dayanarak, içerik üreticileri için uygulanabilir 5 benzersiz trend stratejisi oluştur.
    Lütfen her madde için akımın ne olduğunu ve nasıl uygulanması gerektiğini teknik olarak açıkla.
    Sadece strateji maddelerini yaz; isim, hitap, giriş veya kapanış cümlesi kurma.
    """
    
    try:
        response = model.generate_content(prompt)
        
        # DOSYA YAZMA GARANTİSİ: Dosya yolunu kesinleştiriyoruz
        # Bu satır ".Robot Hazırlanıyor..." yazısını silip yeni analizi üzerine yazar.
        current_dir = os.getcwd()
        output_file = os.path.join(current_dir, "son_analiz.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"Analiz raporu başarıyla güncellendi: {output_file}")
    except Exception as e:
        print(f"Analiz hatası: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        veri_yakala_ve_analiz_et(api_key)
    else:
        print("Hata: API Key bulunamadı!")
