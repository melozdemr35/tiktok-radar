from google.genai import Client 
import json
import os
import time
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    yakalanan_linkler = set() # Çift kaydı anında engellemek için hızlı hafıza
    su_an = datetime.now()
    # 7 Günlük Hafıza: Sadece 7 günden eski veriler temizlenir
    silme_siniri = (su_an - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Oturum Havuzunu Hazırla
    oturumlar = [os.environ.get(f"TIKTOK_SESSION_{i}") for i in range(1, 6)]
    aktif_oturumlar = [o for o in oturumlar if o]
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- RADAR DERİN TARAMA (CANLI HASAT MODU) BAŞLATILDI ---")

    try:
        with sync_playwright() as p:
            # Playwright'ın "Ben Botum" ibaresini gizleyen ek argüman
            browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"], headless=True)
            
            # --- 60 DAKİKAYI 6 TURDA (HER TUR 10 DK) İŞLEME PLANI ---
            for tur in range(6):
                start_tur = time.time()
                secilen_oturum = random.choice(aktif_oturumlar) if aktif_oturumlar else None
                
                print(f">> Tur {tur+1} Başlıyor | Oturum: {'Aktif' if secilen_oturum else 'Anonim'}")
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                    locale="tr-TR"
                )

                # Webdriver izini tamamen sil (Anti-Bot Güvenliği)
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                if secilen_oturum:
                    context.add_cookies([{
                        'name': 'sessionid', 'value': secilen_oturum,
                        'domain': '.tiktok.com', 'path': '/', 'secure': True, 'httpOnly': True
                    }])

                page = context.new_page()
                page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=120000)
                time.sleep(12) 

                # --- TUR İÇİ AGRESİF KAZIMA VE ANLIK TOPLAMA ---
                while (time.time() - start_tur) < 540: 
                    page.keyboard.press("End")
                    page.mouse.wheel(0, random.randint(5000, 9000))
                    time.sleep(random.uniform(4, 7))
                    
                    if random.random() > 0.8:
                        page.mouse.wheel(0, -2000)
                        time.sleep(1)
                        page.keyboard.press("End")

                    # TİKTOK VİDEOLARI SİLMEDEN BİZ ÇEKİYORUZ!
                    items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                            page.query_selector_all('div[class*="DivItemContainerV2"]')
                    
                    eklenen_bu_dongu = 0
                    for item in items:
                        try:
                            link_elem = item.query_selector('a[href*="/video/"]')
                            v_link = link_elem.get_attribute('href') if link_elem else None
                            
                            # Link yoksa veya O ANKİ KASAMIZDA ZATEN VARSA atla
                            if not v_link or v_link in yakalanan_linkler: 
                                continue

                            # Linki kasaya ekle ki bir dahaki kaydırmada tekrar çekmesin
                            yakalanan_linkler.add(v_link)

                            music_elem = item.query_selector('h4') or \
                                         item.query_selector('a[href*="/music/"]') or \
                                         item.query_selector('div[class*="music"]')
                            music_text = music_elem.inner_text().strip() if music_elem else "Popüler Akım"
                            
                            views_elem = item.query_selector('strong[data-e2e="video-views"]') or \
                                         item.query_selector('div[class*="DivCount"]')
                            views_text = views_elem.inner_text() if views_elem else "0"

                            desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]') or item
                            desc_text = desc_elem.inner_text().split('\n')[0]
                            
                            if len(desc_text) > 1:
                                yeni_videolar.append({
                                    "desc": desc_text[:120], 
                                    "music": music_text,
                                    "link": v_link,
                                    "views": views_text,
                                    "paylasim_saati": su_an.strftime('%H:00'),
                                    "tarih": su_an.strftime('%Y-%m-%d'),
                                    "timestamp": time.time()
                                })
                                eklenen_bu_dongu += 1
                        except Exception:
                            continue
                    
                    # Sayıları canlı canlı görmek için loga yazdır
                    if eklenen_bu_dongu > 0:
                        print(f"   [Anlık Hasat] +{eklenen_bu_dongu} yeni -> Toplam Kasa: {len(yeni_videolar)}")

                print(f"Tur {tur+1} bitti. Tur kapanış toplamı: {len(yeni_videolar)}")
                context.close()

            browser.close()
    except Exception as e:
        print(f"Sistem Hatası: {e}")

    # --- VERİTABANI YÖNETİMİ ---
    db_path = "trend_veritabani.json"
    eski_veriler = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: 
                eski_veriler = json.load(f)
            except: 
                eski_veriler = []

    birlesik = yeni_videolar + eski_veriler
    taze = [v for v in birlesik if v.get("tarih", "2000-01-01") >= silme_siniri]
    # Link bazlı ekstra güvenlik tekilleştirmesi
    son_liste = list({v.get('link', ''): v for v in taze if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    
    print(f"\n🏁 FİNAL: {len(yeni_videolar)} video çekildi. Havuzda {len(son_liste)} video var.")

    if api_key and yeni_videolar:
        try:
            client = Client(api_key=api_key)
            analiz_prompt = f"TikTok TR Derin Analiz:\nVeriler: {str(yeni_videolar[:40])}\n\nLütfen trendleri analiz et."
            response = client.models.generate_content(model="gemini-3-flash-preview", contents=analiz_prompt)
            if response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("✅ Profesyonel analiz güncellendi.")
        except: 
            pass

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: 
        veri_yakala_ve_analiz_et(key)
