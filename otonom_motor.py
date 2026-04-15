from google.genai import Client 
import json
import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    su_an = datetime.now()
    silme_siniri = (su_an - timedelta(days=10)).strftime('%Y-%m-%d')
    
    print(f"[{su_an.strftime('%H:%M:%S')}] Derin Radar: Saat ve Link Analizi Başlatıldı...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale="tr-TR"
            )
            page = context.new_page()
            
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=90000)
            time.sleep(12) 
            
            # --- YAVAŞ VE DERİN TARAMA ---
            for i in range(35): 
                page.mouse.wheel(0, 4000)
                time.sleep(2.5) 
                if i % 10 == 0:
                    print(f"Tarama Derinliği: %{int(((i+1)/35)*100)}")
            
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            for item in items:
                try:
                    # 1. Video Linki
                    link_elem = item.query_selector('a[href*="/video/"]')
                    v_link = link_elem.get_attribute('href') if link_elem else None
                    if not v_link: continue

                    # 2. Gerçek Müzik İsmi
                    music_elem = item.query_selector('a[href*="/music/"]') or \
                                 item.query_selector('h4') or \
                                 item.query_selector('div[class*="music"]')
                    music_text = music_elem.inner_text().strip() if music_elem else "Popüler Akım"
                    
                    # 3. İzlenme Sayısı
                    views_elem = item.query_selector('strong[data-e2e="video-views"]') or \
                                 item.query_selector('div[class*="DivCount"]')
                    views_text = views_elem.inner_text() if views_elem else "0"

                    # 4. PAYLAŞIM SAATİ TAHMİNİ (Grafik İçin Kritik)
                    time_tag = item.query_selector('div[class*="DivTimeTag"]') or \
                               item.query_selector('span[class*="Time"]')
                    raw_time = time_tag.inner_text() if time_tag else "1h ago"
                    
                    tahmini_saat = su_an.strftime('%H:00')
                    try:
                        if 'h' in raw_time:
                            ago = int(''.join(filter(str.isdigit, raw_time)))
                            tahmini_saat = (su_an - timedelta(hours=ago)).strftime('%H:00')
                        elif 'm' in raw_time:
                            tahmini_saat = su_an.strftime('%H:00')
                    except: pass

                    desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]') or item
                    desc_text = desc_elem.inner_text().split('\n')[0]
                    
                    if len(desc_text) > 2:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text,
                            "link": v_link,
                            "views": views_text,
                            "paylasim_saati": tahmini_saat, # Grafik bu veriyi kullanacak
                            "timestamp": su_an.strftime('%Y-%m-%d %H:%M:%S'),
                            "tarih": su_an.strftime('%Y-%m-%d')
                        })
                except: continue
            
            browser.close()
    except Exception as e:
        print(f"Bot Motoru Hatası: {e}")

    # --- VERİTABANI YÖNETİMİ ---
    db_path = "trend_veritabani.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []

    birlesik = yeni_videolar + eski_veriler
    taze = [v for v in birlesik if v.get("tarih", "2000-01-01") >= silme_siniri]
    son_liste = list({v.get('link', ''): v for v in taze if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)

    # --- GEMINI 3 STRATEJİ RAPORU ---
    if api_key and yeni_videolar:
        try:
            client = Client(api_key=api_key)
            analiz_prompt = f"""
            TikTok Trend Raporu Hazırla:
            Veriler: {str(yeni_videolar[:25])}
            
            1. Haftanın Popüler İçerik Tarzı (En çok tutan konsept).
            2. Neden Tutuyor? (Psikolojik analiz).
            3. Örnek Video Linki ve Kullanılan Ses İsmi.
            4. En Verimli Paylaşım Saat Aralığı (Verilerdeki paylasim_saati değerlerine göre).
            5. İçerik üreticileri için 3 Altın Taktik.
            """
            response = client.models.generate_content(model="gemini-3-flash-preview", contents=analiz_prompt)
            if response and response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("✅ Gemini 3 analizi tamamladı.")
        except Exception as e: print(f"❌ Analiz Hatası: {e}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: veri_yakala_ve_analiz_et(key)
