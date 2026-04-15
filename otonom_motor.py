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
            # Tarayıcıyı daha gerçekçi bir User-Agent ile başlatıyoruz
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
            
            # TikTok Keşfet'e giriş
            print("Sayfa yükleniyor...")
            page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=120000)
            
            # Sayfa ilk açıldığında bot kontrolünü şaşırtmak için ufak hareketler
            time.sleep(10)
            page.mouse.wheel(0, 400)
            time.sleep(2)

            # --- VERİ SÖKEN AKILLI DÖNGÜ (GÜNCELLENDİ) ---
            print("Veri hacmi artırılıyor, lütfen bekleyin...")
            
            for i in range(120): # 120 kaliteli adım (yaklaşık 12-14 dk)
                # 1. Sayfanın en altına 'End' ile zorla (Yeni videoları tetikler)
                page.keyboard.press("End")
                
                # 2. Rastgele kaydırma miktarı
                page.mouse.wheel(0, random.randint(4000, 7000))
                
                # 3. TikTok'un paketleri yüklemesi için değişken bekleme
                if i % 3 == 0:
                    time.sleep(random.uniform(3.5, 5.5)) 
                else:
                    time.sleep(random.uniform(1.2, 2.2))
                
                # 4. Her 20 adımda bir o anki video sayısını logla
                if i % 20 == 0:
                    gecici_items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                                   page.query_selector_all('div[class*="DivItemContainerV2"]')
                    print(f"Hacim Analizi: %{int(((i+1)/120)*100)} | Şu an sayfada yüklenen: {len(gecici_items)} video")
                    
                    # Eğer hala 0 ise sayfayı bir tık yukarı kaydırıp TikTok'u dürtüyoruz
                    if len(gecici_items) == 0:
                        page.mouse.wheel(0, -1500)
                        time.sleep(3)

            # TÜM KAYDIRMA BİTTİ, VERİLERİ TOPLA
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama Bitti. {len(items)} element işleniyor...")

            for item in items:
                try:
                    # Video Linki
                    link_elem = item.query_selector('a[href*="/video/"]')
                    v_link = link_elem.get_attribute('href') if link_elem else None
                    if not v_link: continue

                    # Müzik Bilgisi
                    music_elem = item.query_selector('a[href*="/music/"]') or item.query_selector('h4')
                    music_text = music_elem.inner_text().strip() if music_elem else "Popüler Akım"
                    
                    # İzlenme
                    views_elem = item.query_selector('strong[data-e2e="video-views"]') or item.query_selector('div[class*="DivCount"]')
                    views_text = views_elem.inner_text() if views_elem else "0"

                    # Paylaşım Saati Tahmini
                    time_tag = item.query_selector('div[class*="DivTimeTag"]') or item.query_selector('span[class*="Time"]')
                    raw_time = time_tag.inner_text() if time_tag else "1h ago"
                    
                    tahmini_saat = su_an.strftime('%H:00')
                    try:
                        if 'h' in raw_time:
                            ago = int(''.join(filter(str.isdigit, raw_time)))
                            tahmini_saat = (su_an - timedelta(hours=ago)).strftime('%H:00')
                    except: pass

                    desc_elem = item.query_selector('div[data-e2e="explore
