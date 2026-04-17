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
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- ULTIMATE MOTOR v2.2: ZIRHLI & TAMIRLI HASAT ---")

    try:
        with sync_playwright() as p:
            # Otomasyon tespitini engellemek için özel argümanlar
            browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"], headless=True)
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800},
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                geolocation={"longitude": 34.9537, "latitude": 40.5506}, 
                permissions=["geolocation"]
            )

            # --- COOKIES TAMİR VE YÜKLEME ---
            if os.path.exists("cookies.json"):
                try:
                    with open("cookies.json", "r", encoding="utf-8") as f:
                        raw_cookies = json.load(f)
                        fixed_cookies = []
                        for c in raw_cookies:
                            if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                                c['sameSite'] = "None"
                            fixed_cookies.append(c)
                        context.add_cookies(fixed_cookies)
                    print("✅ TR Kimlik Kartı başarıyla tamir edildi ve yüklendi!")
                except Exception as e:
                    print(f"❌ Cookies yükleme hatası: {e}")
            else:
                print("⚠️ Uyarı: cookies.json bulunamadı!")

            page = context.new_page()

            try:
                # TR Keşfeti için doğrudan link
                print("🌐 TikTok Keşfet'e bağlanılıyor...")
                page.goto("https://www.tiktok.com/explore?lang=tr-TR", wait_until="networkidle", timeout=60000)
                time.sleep(12)

                # İlk videoyu bul ve tıkla
                try:
                    page.locator('div[data-e2e="explore-item"]').first.click()
                except:
                    page.keyboard.press("ArrowDown")
                
                print("🚀 Derin hasat başladı... Takılmalar otomatik aşılacak.")
                time.sleep(5)

                hatali_kaydirma = 0 
                start_time = time.time()

                # Yaklaşık 45-50 dakika boyunca çalışır
                while (time.time() - start_time) < 4500:
                    v_link = page.url
                    
                    if "/video/" in v_link and v_link not in yakalanan_linkler:
                        yakalanan_linkler.add(v_link)
                        hatali_kaydirma = 0 

                        # Veri Çekme
                        detaylar = page.evaluate('''() => {
                            return {
                                likes: document.querySelector('[data-e2e="browse-like-count"]')?.innerText || "0",
                                comments: document.querySelector('[data-e2e="browse-comment-count"]')?.innerText || "0",
                                desc: document.querySelector('[data-e2e="browse-video-desc"]')?.innerText || "",
                                music: document.querySelector('h4[data-e2e="browse-music"]')?.innerText || "Orijinal Ses"
                            }
                        }''')

                        yeni_videolar.append({
                            "desc": detaylar['desc'][:120],
                            "hashtags": re.findall(r'#\w+', detaylar['desc']),
                            "music": detaylar['music'],
                            "link": v_link,
                            "likes": detaylar['likes'],
                            "comments": detaylar['comments'],
                            "kayit_saati": datetime.now().strftime('%H:00'),
                            "tarih": datetime.now().strftime('%Y-%m-%d')
                        })
                        
                        if len(yeni_videolar) % 20 == 0:
                            print(f"📊 Mevcut Durum: {len(yeni_videolar)} video toplandı...")

                    # --- AKILLI KAYDIRMA (ZIRHLI MOD) ---
                    # Hem tuşla hem mouse tekerleğiyle kaydırıyoruz
                    page.keyboard.press("ArrowDown")
time.sleep(0.5)
page.keyboard.press("ArrowDown")
page.mouse.wheel(0, 1000) 
                    
                    # İzleme simülasyonu için rastgele bekleme
                    time.sleep(random.uniform(3.0, 6.0)) 
                    
                    if page.url == v_link:
                        hatali_kaydirma += 1
                        if hatali_kaydirma >= 3:
                            print("🔄 Akış takıldı, sayfa yenileniyor (Auto-Refresh)...")
                            page.reload()
                            time.sleep(10)
                            hatali_kaydirma = 0
                            # Yenileme sonrası ilk videoya tekrar odaklan
                            try: page.locator('div[data-e2e="explore-item"]').first.click()
                            except: pass

                if len(yeni_videolar) >= 600:
                    print("🎯 Hedeflenen hasat miktarına ulaşıldı.")

            except Exception as e:
                print(f"❌ Tarayıcı hatası: {e}")

            context.close()
            browser.close()
    except Exception as e:
        print(f"!!! KRITIK HATA: {e}")

    # --- VERİLERİ VERİTABANINA YAZ ---
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
    
    print(f"\n🏁 İŞLEM TAMAMLANDI: {len(yeni_videolar)} yeni video eklendi!")
    print(f"📂 Toplam Havuz Büyüklüğü: {len(son_liste)}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    veri_yakala_ve_analiz_et(key)
