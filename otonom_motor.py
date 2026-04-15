import google.generativeai as genai
import json
import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    su_an = datetime.now()
    # 10 günlük silme sınırı
    silme_siniri = (su_an - timedelta(days=10)).strftime('%Y-%m-%d')
    
    print(f"[{su_an.strftime('%H:%M:%S')}] TikTok Derin Radar Başlatıldı... (10 Günlük Bellek)")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            # TikTok Keşfet
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=90000)
            time.sleep(10) # Sayfanın oturması için tam mola
            
            # --- AGRESİF TARAMA: 25 KEZ KAYDIRMA (Daha çok veri için) ---
            print("Türkiye Keşfeti taranıyor, aşağılara iniliyor...")
            for i in range(25):
                page.mouse.wheel(0, 6000) # Kaydırma mesafesi artırıldı
                time.sleep(1.5) # Hızlı ama güvenli kaydırma
                if i % 5 == 0:
                    print(f"Tarama Derinliği: %{int(((i+1)/25)*100)}")
            
            # Video elementlerini yakala
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"Sistemde saptanan potansiyel video sayısı: {len(items)}")

            for item in items:
                try:
                    # Açıklama ve Müzik çekme
                    all_text = item.inner_text().split('\n')
                    desc_text = all_text[0] if all_text else ""
                    
                    music_elem = item.query_selector('h4') or item.query_selector('div[class*="music"]')
                    music_text = music_elem.inner_text() if music_elem else "Popüler Akım"
                    
                    if len(desc_text) > 3:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text,
                            "tarih": su_an.strftime('%Y-%m-%d'),
                            "hashtagler": "Trend Radarı"
                        })
                except: continue
            
            browser.close()
    except Exception as e:
        print(f"Bot Hatası: {e}")

    # --- VERİTABANI YÖNETİMİ (10 GÜNLÜK OTOMATİK TEMİZLİK) ---
    db_path = "trend_veritabani.json"
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []

    # Yeni ve eskileri birleştir, 10 günden eski olanları at
    birlesik_liste = yeni_videolar + eski_veriler
    # Sadece 10 gün içindeki verileri tut
    guncel_ve_taze = [v for v in birlesik_liste if v.get("tarih", "2000-01-01") >= silme_siniri]
    
    # Aynı videoları (açıklama bazlı) temizle
    son_liste = list({v['desc']: v for v in guncel_ve_taze}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    
    print(f"İşlem Başarılı! {len(yeni_videolar)} yeni eklendi. Toplam aktif kayıt: {len(son_liste)}")

    # --- GEMINI ANALİZ (404 HATASI KESİN ÇÖZÜM) ---
    if api_key and len(yeni_videolar) > 0:
        try:
            genai.configure(api_key=api_key)
            # 404 almamak için en stabil model ismini kullanıyoruz
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            analiz_prompt = f"Şu an TikTok'ta patlayan şu videoları analiz et ve içerik üreticileri için 5 kısa, vurucu strateji yaz: {str(yeni_videolar[:30])}"
            
            # API sürüm hatasını bypass etmek için direkt üretim
            response = model.generate_content(analiz_prompt)
            
            if response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("Gemini raporu başarıyla hazırladı.")
        except Exception as e:
            print(f"Gemini Rapor Hatası: {e}")

if __name__ == "__main__":
    veri_yakala_ve_after = os.environ.get("GEMINI_API_KEY")
    veri_yakala_ve_analiz_et(veri_yakala_ve_after)
