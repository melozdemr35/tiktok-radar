from google.genai import Client 
import json
import os
import time
import random
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    yakalanan_linkler = set()
    su_an = datetime.now()
    silme_siniri = (su_an - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # 1. GÜVENLİK KONTROLÜ: Oturumları çek
    oturumlar = [os.environ.get(f"TIKTOK_SESSION_{i}") for i in range(1, 6)]
    aktif_oturumlar = [o for o in oturumlar if o]
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- MOTOR ATEŞLENDİ: OPERASYON BAŞLIYOR ---")
    print(f"Aktif Oturum Sayısı: {len(aktif_oturumlar)}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"], headless=True)
            
            for tur in range(6):
                start_tur = time.time()
                secilen_oturum = random.choice(aktif_oturumlar) if aktif_oturumlar else None
                
                print(f"\n>> Tur {tur+1} Başlatılıyor...")
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 800},
                    locale="tr-TR"
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                if secilen_oturum:
                    context.add_cookies([{'name': 'sessionid', 'value': secilen_oturum, 'domain': '.tiktok.com', 'path': '/', 'secure': True, 'httpOnly': True}])

                page = context.new_page()

                # 2. ANA DÖNGÜ: Sayfa Yenileme ve Derin Hasat
                while (time.time() - start_tur) < 540:
                    try:
                        print(f"   [F5] Keşfet yenileniyor: {datetime.now().strftime('%H:%M:%S')}")
                        page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=90000)
                        time.sleep(10)

                        # Vitrin hasadı için hafif kaydır
                        page.keyboard.press("End")
                        time.sleep(3)

                        items = page.query_selector_all('div[data-e2e="explore-item"]')
                        
                        for item in items:
                            try:
                                link_elem = item.query_selector('a[href*="/video/"]')
                                v_link = link_elem.get_attribute('href') if link_elem else None
                                
                                if not v_link or v_link in yakalanan_linkler: 
                                    continue

                                yakalanan_linkler.add(v_link)

                                # VİDEO İÇİNE GİRİŞ (DERİN ANALİZ)
                                page.goto(v_link, wait_until="domcontentloaded", timeout=45000)
                                time.sleep(4)

                                # Verileri sök
                                detaylar = page.evaluate('''() => {
                                    return {
                                        likes: document.querySelector('[data-e2e="like-count"]')?.innerText || "0",
                                        comments: document.querySelector('[data-e2e="comment-count"]')?.innerText || "0",
                                        music: document.querySelector('[data-e2e="browse-music"]')?.innerText.trim() || "Popüler Akım",
                                        musicUsage: document.querySelector('[data-e2e="browse-music-usage"]')?.innerText || "Az Kullanım",
                                        desc: document.querySelector('[data-e2e="browse-video-desc"]')?.innerText || "",
                                        vTime: document.querySelector('span[data-e2e="browser-nickname"] + span + span')?.innerText || "Yeni"
                                    }
                                }''')

                                yeni_videolar.append({
                                    "desc": detaylar['desc'][:120],
                                    "hashtags": re.findall(r'#\w+', detaylar['desc']),
                                    "music": detaylar['music'],
                                    "music_usage": detaylar['musicUsage'],
                                    "link": v_link,
                                    "likes": detaylar['likes'],
                                    "comments": detaylar['comments'],
                                    "paylasim_saati": detaylar['vTime'],
                                    "kayit_saati": datetime.now().strftime('%H:%M'),
                                    "tarih": su_an.strftime('%Y-%m-%d')
                                })
                                print(f"      [Hasat Başarılı] Saat: {detaylar['vTime']} | Beğeni: {detaylar['likes']}")
                                
                                # Ana sayfaya geri dönmek yerine diğer yenilemeyi bekle
                                if len(yeni_videolar) % 10 == 0: break 

                            except: continue

                        time.sleep(random.uniform(5, 8))
                    except:
                        print("   [Uyarı] Döngüde anlık aksama, yeniden deneniyor...")
                        time.sleep(10)

                context.close()
            browser.close()
    except Exception as e:
        print(f"!!! KRİTİK HATA: {e}")

    # --- VERİTABANI YÖNETİMİ ---
    db_path = "trend_veritabani.json"
    eski_veriler = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: eski_veriler = json.load(f)
            except: eski_veriler = []

    birlesik = yeni_videolar + eski_veriler
    taze = [v for v in birlesik if v.get("tarih", "2000-01-01") >= silme_siniri]
    son_liste = list({v.get('link', ''): v for v in taze if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    
    print(f"\n🏁 FİNAL: {len(yeni_videolar)} video detaylıca işlendi. Havuz: {len(son_liste)}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: veri_yakala_ve_analiz_et(key)
