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
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- ULTIMATE MOTOR v3.4: KRIZ PROTOKOLU AKTIF ---")
    print(f"📅 Sistem {silme_siniri} tarihinden eski tüm videoları temizleyecek.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"], headless=True)
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800},
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                geolocation={"longitude": 34.9537, "latitude": 40.5506}, 
                permissions=["geolocation"]
            )

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
                    print("✅ TR Kimlik Aktif. Akıllı kaçış modu devrede.")
                except Exception as e:
                    print(f"❌ Cookies hatası: {e}")

            page = context.new_page()

            try:
                page.goto("https://www.tiktok.com/explore?lang=tr-TR", wait_until="networkidle", timeout=60000)
                time.sleep(12)

                try:
                    page.locator('div[data-e2e="explore-item"]').first.click()
                except:
                    page.keyboard.press("ArrowDown")
                
                print("🚀 Hasat başladı. Hedef: Güvenlik duvarına kadar maksimum video.")
                time.sleep(5)

                hatali_kaydirma = 0 
                kriz_sayaci = 0 # 🛡️ YENİ: Kriz sayacı eklendi
                start_time = time.time()

                while (time.time() - start_time) < 4500:
                    v_link = page.url
                    
                    if "/video/" in v_link and v_link not in yakalanan_linkler:
                        yakalanan_linkler.add(v_link)
                        hatali_kaydirma = 0 
                        kriz_sayaci = 0 # Yeni video bulunduysa krizi sıfırla

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
                        
                        if len(yeni_videolar) % 50 == 0:
                            print(f"📊 Mevcut Durum: {len(yeni_videolar)} video toplandı...")

                    page.keyboard.press("ArrowDown")
                    page.mouse.wheel(0, 850) 
                    time.sleep(random.uniform(4.5, 7.5)) 
                    
                    if page.url == v_link:
                        hatali_kaydirma += 1
                        if hatali_kaydirma >= 3: 
                            kriz_sayaci += 1
                            
                            # 🛡️ YENİ: Eğer duvar aşılamıyorsa döngüyü şıkça bitir
                            if kriz_sayaci >= 4:
                                print("🚨 TikTok duvarı aşılamadı (Muhtemel Captcha/Login Pop-up). Kurtarma iptal ediliyor.")
                                print(f"✅ Mevcut {len(yeni_videolar)} video hasatı kurtarıldı. Kayıt aşamasına geçiliyor...")
                                break
                                
                            print(f"🔄 Akış tıkandı! (Deneme {kriz_sayaci}/4) Keşfet'e reset atılıyor...")
                            try:
                                page.goto("https://www.tiktok.com/explore?lang=tr-TR", wait_until="networkidle", timeout=30000)
                                time.sleep(10)
                                # 🛡️ YENİ: Ekranda Pop-up varsa kapatmayı dene
                                page.keyboard.press("Escape")
                                time.sleep(2)
                                page.locator('div[data-e2e="explore-item"]').first.click()
                                print("✨ Yeni akış başarıyla başlatıldı.")
                                time.sleep(5)
                            except:
                                page.reload()
                            hatali_kaydirma = 0

                if len(yeni_videolar) >= 1500:
                    print("🎯 Üst limit hasat tamamlandı.")

            except Exception as e:
                print(f"❌ Tarayıcı hatası: {e}")

            context.close()
            browser.close()
    except Exception as e:
        print(f"!!! KRITIK HATA: {e}")

    db_path = "trend_veritabani.json"
    eski_veriler = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: 
                eski_veriler = json.load(f)
            except: 
                eski_veriler = []

    guncel_eski_veriler = [v for v in eski_veriler if v.get('tarih', '') >= silme_siniri]
    silinen_sayisi = len(eski_veriler) - len(guncel_eski_veriler)

    son_liste = list({v.get('link', ''): v for v in (yeni_videolar + guncel_eski_veriler) if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    
    print(f"\n🏁 İŞLEM TAMAMLANDI: {len(yeni_videolar)} yeni video eklendi!")
    if silinen_sayisi > 0:
        print(f"🗑️ 7 günden eski {silinen_sayisi} video veritabanından silindi.")
    print(f"📂 Toplam Havuz Büyüklüğü: {len(son_liste)}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: veri_yakala_ve_analiz_et(key)
