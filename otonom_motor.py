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
    # Veritabanını her taramada SİLMİYORUZ, sadece 7 günden eskiyi temizliyoruz
    silme_siniri = (su_an - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"[{su_an.strftime('%H:%M:%S')}] --- RADAR DERİN TARAMA (60 DK) BAŞLATILDI ---")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                locale="tr-TR"
            )

            # Oturum Enjeksiyonu
            oturumlar = [os.environ.get(f"TIKTOK_SESSION_{i}") for i in range(1, 6)]
            aktif_oturumlar = [o for o in oturumlar if o]
            secilen_oturum = random.choice(aktif_oturumlar) if aktif_oturumlar else None
            
            if secilen_oturum:
                context.add_cookies([{
                    'name': 'sessionid', 'value': secilen_oturum,
                    'domain': '.tiktok.com', 'path': '/', 'secure': True, 'httpOnly': True
                }])

            page = context.new_page()
            page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=120000)
            time.sleep(15)

            # --- 60 DAKİKALIK ZAMAN ODAKLI AGRESİF TARAMA ---
            # 42 videoda takılmayı önleyen 'Sürekli Tetikleme' mekanizması
            start_time = time.time()
            lap = 0
            print("Veri madenciliği başladı, 55 dakika boyunca kazıma yapılacak...")
            
            while (time.time() - start_time) < 3300: # 55 dakika aktif tarama
                page.keyboard.press("End")
                # TikTok paketlerini zorla yükletmek için rastgele scroll zıplamaları
                page.mouse.wheel(0, random.randint(4000, 8000))
                
                # Yeni videoların DOM'a düşmesi için değişken bekleme
                time.sleep(random.uniform(5, 9)) 
                
                lap += 1
                if lap % 10 == 0:
                    gecici = page.query_selector_all('div[data-e2e="explore-item"]') or \
                             page.query_selector_all('div[class*="DivItemContainerV2"]')
                    print(f"Dakika: {int((time.time()-start_time)/60)} | Yüklenen Video: {len(gecici)}")
                    
                    # Eğer yükleme hızı çok yavaşsa sayfayı yukarı-aşağı yaparak TikTok'u dürt
                    if len(gecici) < (lap * 2):
                        page.mouse.wheel(0, -3000)
                        time.sleep(2)
                        page.keyboard.press("End")

            # --- VERİ KAZIMA (SCRAPING) AŞAMASI ---
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama Bitti. {len(items)} element veriye dönüştürülüyor...")

            for item in items:
                try:
                    # 1. Video Linki (Dashboard listesi için)
                    link_elem = item.query_selector('a[href*="/video/"]')
                    v_link = link_elem.get_attribute('href') if link_elem else None
                    if not v_link: continue

                    # 2. Müzik/Akım Adı (Sayı çıkma hatasını gideren geliştirilmiş seçici)
                    music_elem = item.query_selector('h4') or \
                                 item.query_selector('a[href*="/music/"]') or \
                                 item.query_selector('div[class*="music"]')
                    music_text = music_elem.inner_text().strip() if music_elem else "Popüler Akım"
                    
                    # 3. İzlenme Sayısı
                    views_elem = item.query_selector('strong[data-e2e="video-views"]') or \
                                 item.query_selector('div[class*="DivCount"]')
                    views_text = views_elem.inner_text() if views_elem else "0"

                    # 4. Açıklama (Dashbord detay listesi için)
                    desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]') or item
                    desc_text = desc_elem.inner_text().split('\n')[0]
                    
                    if len(desc_text) > 2:
                        yeni_videolar.append({
                            "desc": desc_text[:120], 
                            "music": music_text,
                            "link": v_link,
                            "views": views_text,
                            "paylasim_saati": su_an.strftime('%H:00'),
                            "tarih": su_an.strftime('%Y-%m-%d'),
                            "timestamp": time.time()
                        })
                except: continue
            
            browser.close()
    except Exception as e:
        print(f"Sistem Hatası: {e}")

    # --- VERİTABANI YÖNETİMİ (Kümülatif Ekleme Mantığı) ---
    db_path = "trend_veritabani.json"
    eski_veriler = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: eski_veriler = json.load(f)
            except: eski_veriler = []

    # Yeni verileri eskilere ekle
    birlesik = yeni_videolar + eski_veriler
    
    # SADECE 7 GÜNLÜK VERİLERİ TUT (Eski taramaları silmez, sadece süresi dolanı siler)
    taze = [v for v in birlesik if v.get("tarih", "2000-01-01") >= silme_siniri]
    
    # Link bazlı tekilleştirme (Aynı video havuza 2 kez girmesin)
    son_liste = list({v.get('link', ''): v for v in taze if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    
    print(f"🏁 SONUÇ: Bu taramada {len(yeni_videolar)} video yakalandı.")
    print(f"📦 TOPLAM HAVUZ: {len(son_liste)} eşsiz trend video (7 Günlük Hafıza).")

    # --- GEMINI 3 STRATEJİ RAPORU ---
    if api_key and yeni_videolar:
        try:
            client = Client(api_key=api_key)
            analiz_prompt = f"TikTok TR Derin Analiz:\nVeriler: {str(yeni_videolar[:40])}\n\n1. Popüler Konsept\n2. Neden Tutuyor?\n3. Link ve Ses Örneği\n4. En İyi Paylaşım Saati\n5. 3 Altın Taktik"
            response = client.models.generate_content(model="gemini-3-flash-preview", contents=analiz_prompt)
            if response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("✅ Profesyonel analiz güncellendi.")
        except: pass

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key: veri_yakala_ve_analiz_et(key)
