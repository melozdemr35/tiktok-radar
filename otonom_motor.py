import google.generativeai as genai
import json
import os
import time
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    
    print("TikTok Keşfet'e 'Ultra Görünmezlik' ile sızılıyor...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Gerçek bir bilgisayar tarayıcısı gibi davran (User-Agent ve Screen Size)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
            page = context.new_page()
            
            # TikTok'a git ve sayfa içeriğinin kabaca oluşmasını bekle
            page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=90000)
            
            # --- KRİTİK: SAYFAYI DİNLENDİRME ---
            print("Sayfa açıldı, elemanların yüklenmesi için 10 saniye bekleniyor...")
            time.sleep(10) 
            
            # --- YAVAŞ VE İNSANSI KAYDIRMA ---
            for i in range(10): 
                page.mouse.wheel(0, 3000)
                time.sleep(3) # TikTok bot sanmasın diye her kaydırmada 3 sn durakla
                if i % 2 == 0:
                    print(f"Tarama ilerlemesi: %{int(((i+1)/10)*100)}")
            
            # Eleman seçicileri daha esnek hale getirdik (TikTok güncellemelerine karşı)
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"Sistemde bulunan ham element sayısı: {len(items)}")
            
            for item in items[:200]:
                try:
                    # Yazıyı ve müziği daha derinlemesine ara
                    desc_text = item.inner_text().split('\n')[0] if item else ""
                    
                    # Şarkı bulucu (daha esnek seçici)
                    music_elem = item.query_selector('h4') or item.query_selector('div[class*="music"]')
                    music_text = music_elem.inner_text() if music_elem else "Trend Müzik"
                    
                    if len(desc_text) > 3:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text,
                            "hashtagler": "Canlı Keşfet"
                        })
                except:
                    continue
            
            browser.close()
            print(f"İşlem Tamam! {len(yeni_videolar)} taze veri toplandı.")
    except Exception as e:
        print(f"Veri çekme sırasında hata: {e}")

    # --- VERİTABANI GÜNCELLEME ---
    db_path = "trend_veritabani.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []
    
    if len(yeni_videolar) > 0:
        guncel_liste = yeni_videolar + eski_veriler
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(guncel_liste[:10000], f, ensure_ascii=False, indent=4)
        print(f"Veritabanı güncellendi. Toplam kayıt: {len(guncel_liste)}")
    else:
        print("❌ Dikkat: Yeni veri yakalanamadı, veritabanı aynı kaldı.")

    # --- GEMINI ANALİZ (Hata giderilmiş versiyon) ---
    if api_key and len(yeni_videolar) > 0:
        try:
            genai.configure(api_key=api_key)
            # Model ismini v1beta yerine en kararlı sürüme çektik
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            analiz_prompt = f"Şu TikTok trendlerini analiz et ve içerik üreticileri için 5 kısa strateji yaz: {str(yeni_videolar[:20])}"
            response = model.generate_content(analiz_prompt)
            
            with open("son_analiz.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Gemini analizi başarıyla tamamladı.")
        except Exception as e:
            print(f"Gemini Analiz Hatası: {e}")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    veri_yakala_ve_analiz_et(api_key)
