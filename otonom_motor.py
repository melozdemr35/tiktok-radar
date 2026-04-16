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
    
    oturumlar = [os.environ.get(f"TIKTOK_SESSION_{i}") for i in range(1, 6)]
    aktif_oturumlar = [o for o in oturumlar if o]
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- MOTOR ATEŞLENDİ: AKILLI KAÇIŞ VE SWIPE MODU ---")

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

                try:
                    # SİSTEM GİRİŞİ
                    page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=60000)
                    time.sleep(8)

                    # İlk videoya tıkla ve tam ekran oynatıcıyı aç
                    page.locator('div[data-e2e="explore-item"]').first.click()
                    print("   [Oynatıcı] Video açıldı, kaydırma (swipe) başlıyor...")
                    time.sleep(5)

                    hatali_kaydirma = 0 # Engel sayacı eklendi

                    # 9 DAKİKALIK ANA DÖNGÜ
                    while (time.time() - start_tur) < 540:
                        v_link = page.url
                        
                        if "/video/" in v_link and v_link not in yakalanan_linkler:
                            yakalanan_linkler.add(v_link)
                            hatali_kaydirma = 0 # Video başarıyla açıldıysa sayacı sıfırla

                            # JAVASCRIPT İLE DERİN VERİ SÖKÜMÜ
                            detaylar = page.evaluate('''() => {
                                // Müzik ismini bul, bulamazsa senin istediğin gibi direkt "Orijinal Ses" yazıp geç
                                let musicEl = document.querySelector('h4[data-e2e="browse-music"]') || 
                                              document.querySelector('a[href*="/music/"]') || 
                                              document.querySelector('div[class*="music"]');
                                
                                let musicName = musicEl ? musicEl.innerText.trim().replace(/\\n/g, '') : "Orijinal Ses";
                                if (musicName.match(/^[\d\.]+[KM]?$/)) { musicName = "Orijinal Ses"; } // Hatalı sayı gelirse ez

                                return {
                                    likes: document.querySelector('[data-e2e="like-count"]')?.innerText || "0",
                                    comments: document.querySelector('[data-e2e="comment-count"]')?.innerText || "0",
                                    music: musicName,
                                    musicUsage: document.querySelector('[data-e2e="browse-music-usage"]')?.innerText || "Bilinmiyor",
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
                                "kayit_saati": datetime.now().strftime('%H:00'),
                                "tarih": su_an.strftime('%Y-%m-%d')
                            })
                            
                            if len(yeni_videolar) % 20 == 0:
                                print(f"      [Hızlı Swipe] Toplanan: {len(yeni_videolar)} video...")

                        # Sıradaki videoya geç
                        page.mouse.click(640, 400) # Ekranın ortasına tıkla (Popup çıkarsa kapatır)
                        time.sleep(0.5)
                        page.keyboard.press("ArrowDown")
                        time.sleep(random.uniform(2.0, 3.5)) 
                        
                        # --- TAKILMA VE AKILLI KAÇIŞ KONTROLÜ ---
                        if page.url == v_link:
                             hatali_kaydirma += 1
                             page.mouse.wheel(0, 1000) # Tekerlek ile zorla kaydırmayı dene
                             time.sleep(2)
                             
                             if hatali_kaydirma >= 3:
                                 print("      [Sistem Uyarı] Bu oturum kilitlendi (Giriş engeli). Hemen diğer tura geçiliyor...")
                                 break # Döngüyü kırar ve direkt sonraki Tura geçer. Zaman kaybını önler!

                except Exception as e:
                    print(f"   [Uyarı] Tur içinde aksama: {e}")

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
    
    print(f"\n🏁 FİNAL: {len(yeni_videolar)} video hızla çekildi. Havuz: {len(son_liste)}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: veri_yakala_ve_analiz_et(key)
