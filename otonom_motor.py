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
    # 7 Günlük Hafıza: Sadece 7 günden eski veriler temizlenir
    silme_siniri = (su_an - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Oturum Havuzunu Hazırla (GitHub Secrets üzerinden gelen 5 oturum)
    oturumlar = [os.environ.get(f"TIKTOK_SESSION_{i}") for i in range(1, 6)]
    aktif_oturumlar = [o for o in oturumlar if o]
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- RADAR DERİN TARAMA (1000+ HEDEF) BAŞLATILDI ---")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # --- 60 DAKİKAYI 6 TURDA (HER TUR 10 DK) İŞLEME PLANI ---
            # TikTok'un 42 videodan sonra 'musluğu kapatmasını' sayfayı yenileyerek aşıyoruz.
            for tur in range(6):
                start_tur = time.time()
                secilen_oturum = random.choice(aktif_oturumlar) if aktif_oturumlar else None
                
                print(f">> Tur {tur+1} Başlıyor | Oturum: {'Aktif' if secilen_oturum else 'Anonim'}")
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 720},
                    locale="tr-TR"
                )

                if secilen_oturum:
                    context.add_cookies([{
                        'name': 'sessionid', 'value': secilen_oturum,
                        'domain': '.tiktok.com', 'path': '/', 'secure': True, 'httpOnly': True
                    }])

                page = context.new_page()
                page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=120000)
                time.sleep(12) 

                # Tur içi agresif kazıma (Yaklaşık 9 dakika boyunca)
                lap = 0
                while (time.time() - start_tur) < 540: 
                    page.keyboard.press("End")
                    page.mouse.wheel(0, random.randint(5000, 9000))
                    
                    # Paketlerin yüklenmesi için bekleme
                    time.sleep(random.uniform(4, 7))
                    
                    lap += 1
                    if lap % 15 == 0:
                        # Sayfayı 'canlı' tutmak için hafif yukarı kaydırma
                        page.mouse.wheel(0, -2000)
                        time.sleep(1)
                        page.keyboard.press("End")

                # --- TUR SONU VERİ TOPLAMA ---
                items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                        page.query_selector_all('div[class*="DivItemContainerV2"]')
                
                print(f"Tur {tur+1} bitti. {len(items)} element analiz ediliyor...")

                for item in items:
                    try:
                        link_elem = item.query_selector('a[href*="/video/"]')
                        v_link = link_elem.get
