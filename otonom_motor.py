from google.genai import Client 
import json
import os
import time
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    su_an = datetime.now()
    # Veritabanı dengesi için 7 günlük veri
    silme_siniri = (su_an - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # --- OTURUM HAVUZU ---
    oturumlar = [
        os.environ.get("TIKTOK_SESSION_1"),
        os.environ.get("TIKTOK_SESSION_2"),
        os.environ.get("TIKTOK_SESSION_3"),
        os.environ.get("TIKTOK_SESSION_4"),
        os.environ.get("TIKTOK_SESSION_5")
    ]
    aktif_oturumlar = [o for o in oturumlar if o]
    secilen_oturum = random.choice(aktif_oturumlar) if aktif_oturumlar else None

    print(f"[{su_an.strftime('%H:%M:%S')}] --- RADAR TURBO & GİZLİ MOD AKTİF ---")
    print(f"Hedef: Günlük 10k+ Veri | Oturum: {'Aktif' if secilen_oturum else 'Anonim'}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale="tr-TR"
            )

            if secilen_oturum:
                context.add_cookies([{
                    'name': 'sessionid', 'value': secilen_oturum,
                    'domain': '.tiktok.com', 'path': '/', 'secure': True, 'httpOnly': True
                }])

            page = context.new_page()
            
            print("Sayfa yükleniyor...")
            page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=120000)
            
            time.sleep(10)
            page.mouse.wheel(0, 400)
            time.sleep(2)

            # --- VERİ SÖKEN AKILLI DÖNGÜ ---
            print("Veri hacmi artırılıyor, lütfen bekleyin...")
            
            for i in range(120):
                page.keyboard.press("End")
                page.mouse.wheel(0, random.randint(4000, 7000))
                
                if i % 3 == 0:
                    time.sleep(random.uniform(3.5, 5.5)) 
                else:
                    time.sleep(random.uniform(1.2, 2.2))
                
                if i % 20 == 0:
                    gecici_items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                                   page.query_selector_all('div[class*="DivItemContainerV2"]')
                    print(f"Hacim Analizi: %{int(((i+1)/120)*100)} | Şu an sayfada yüklenen: {len(gecici_items)} video")
                    
                    if len(gecici_items) == 0:
                        page.mouse.wheel(0, -1500)
                        time.sleep(3)

            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama Bitti. {len(items)} element işleniyor...")

            for item in items:
                try:
                    link_elem = item.query_selector('a[href*="/video/"]')
                    v_link = link_elem.get_attribute('href') if link_elem else None
                    if not v_link: continue

                    music_elem = item.query_selector('a[href*="/music/"]') or item.query_selector('h4')
                    music_text = music_elem.inner_text().strip() if music_elem else "Popüler Akım"
                    
                    views_elem = item.query_selector('strong[data-e2e="video-views"]') or item.query_selector('div[class*="DivCount"]')
                    views_text = views_elem.inner_text() if views_elem else "0"

                    time_tag = item.query_selector('div[class*="DivTimeTag"]') or item.query_selector('span[class*="Time"]')
                    raw_time = time_tag.inner_text() if time_tag else "1h ago"
                    
                    tahmini_saat = su_an.strftime('%H:00')
                    try:
                        if 'h' in raw_time:
                            ago = int(''.join(filter(str.isdigit, raw_time)))
                            tahmini_saat = (su_an - timedelta(hours=ago)).strftime('%H:00')
                    except: pass

                    desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]') or item
                    desc_text = desc_elem.inner_text().split('\n')[0]
                    
                    if len(desc_text) > 2:
                        yeni_videolar.append({
                            "desc": desc_text, "music": music_text, "link": v_link,
                            "views": views_text, "paylasim_saati": tahmini_saat,
                            "timestamp": su_an.strftime('%Y-%m-%d %H:%M:%S'),
                            "tarih": su_an.strftime('%Y-%m-%d')
                        })
                except: continue
            
            browser.close()
    except Exception as e:
        print(f"Sistem Hatası: {e}")

    # --- VERİTABANI YÖNETİMİ ---
    db_path = "trend_veritabani.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else: eski_veriler = []

    birlesik = yeni_videolar + eski_veriler
    taze = [v for v in birlesik if v.get("tarih", "2000-01-01") >= silme_siniri]
    son_liste = list({v.get('link', ''): v for v in taze if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    
    print(f"🏁 SONUÇ: Bu taramada {len(yeni_videolar)} video yakalandı.")
    print(f"📦 TOPLAM: Veritabanında {len(son_liste)} adet eşsiz trend video var.")

    # --- GEMINI 3 STRATEJİ RAPORU ---
    if api_key and yeni_videolar:
        try:
            client = Client(api_key=api_key)
            analiz_prompt = f"TikTok TR Derin Keşfet Raporu:\nVeriler: {str(yeni_videolar[:40])}\n\n1. Popüler Konsept\n2. Neden Tutuyor?\n3. Örnek Link ve Ses\n4. Altın Paylaşım Saati\n5. 3 Taktik"
            response = client.models.generate_content(model="gemini-3-flash-preview", contents=analiz_prompt)
            if response and response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("✅ Gemini 3 analizi tamamladı.")
        except Exception as e: print(f"❌ Analiz Hatası: {e}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: veri_yakala_ve_analiz_et(key)
