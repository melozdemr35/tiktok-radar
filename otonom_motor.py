from google.genai import Client 
import json
import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    su_an = datetime.now()
    # 10 günlük silme sınırı
    silme_siniri = (su_an - timedelta(days=10)).strftime('%Y-%m-%d')
    
    print(f"[{su_an.strftime('%H:%M:%S')}] TikTok Derin Radar Başlatıldı... (Link, Müzik ve İzlenme Takibi Aktif)")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale="tr-TR"
            )
            page = context.new_page()
            
            # TikTok Explore
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle", timeout=90000)
            print("Sayfa açıldı, derin tarama ve veri toplama yapılıyor...")
            time.sleep(12) 
            
            # --- YAVAŞ VE DERİN TARAMA (Daha kaliteli ve farklı veri için) ---
            for i in range(35): 
                page.mouse.wheel(0, 4000)
                time.sleep(2.5) 
                if i % 10 == 0:
                    print(f"Tarama Derinliği: %{int(((i+1)/35)*100)}")
            
            # Video elementlerini yakala
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"Sistemde saptanan potansiyel video sayısı: {len(items)}")

            for item in items:
                try:
                    # 1. Video Linkini Yakala (Tıklanabilirlik için)
                    link_elem = item.query_selector('a[href*="/video/"]')
                    v_link = link_elem.get_attribute('href') if link_elem else None
                    if not v_link: continue

                    # 2. Gerçek Müzik İsmini Yakala (Doğrudan müzik linkinden veya h4'ten)
                    music_elem = item.query_selector('a[href*="/music/"]') or \
                                 item.query_selector('h4') or \
                                 item.query_selector('div[class*="music"]')
                    music_text = music_elem.inner_text().strip() if music_elem else "Popüler Akım"
                    
                    # 3. İzlenme Sayısını Yakala (7/3/1 günlük trend analizi için)
                    views_elem = item.query_selector('strong[data-e2e="video-views"]') or \
                                 item.query_selector('div[class*="DivCount"]')
                    views_text = views_elem.inner_text() if views_elem else "0"

                    # 4. Açıklama Metni
                    desc_elem = item.query_selector('div[data-e2e="explore-item-desc"]') or item
                    desc_text = desc_elem.inner_text().split('\n')[0]
                    
                    if len(desc_text) > 2:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text,
                            "link": v_link,
                            "views": views_text,
                            "timestamp": su_an.strftime('%Y-%m-%d %H:%M:%S'), # Dashboard filtreleri için
                            "tarih": su_an.strftime('%Y-%m-%d'),
                            "hashtagler": "Trend Radarı"
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

    # Link bazlı tekilleştirme (Aynı videoyu tekrar ekleme, veriyi güncelle)
    birlesik_liste = yeni_videolar + eski_veriler
    guncel_ve_taze = [v for v in birlesik_liste if v.get("tarih", "2000-01-01") >= silme_siniri]
    
    # Linki anahtar yaparak videoları eşsiz tutuyoruz
    son_liste = list({v.get('link', ''): v for v in guncel_ve_taze if v.get('link')}.values())

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(son_liste, f, ensure_ascii=False, indent=4)
    print(f"İşlem Başarılı! Toplam aktif kayıt: {len(son_liste)}")

    # --- GEMINI 3 ANALİZ (Gelişmiş Strateji Paneli Raporu) ---
    if api_key and yeni_videolar:
        try:
            client = Client(api_key=api_key)
            
            # Gemini'ye gönderilen talimatları senin isteklerine göre özelleştirdim
            analiz_prompt = f"""
            Aşağıdaki TikTok verilerini derinlemesine analiz et ve profesyonel bir radar raporu hazırla:
            Veriler: {str(yeni_videolar[:25])}
            
            Rapor Formatı (Lütfen bu başlıkları kullan):
            1. **Haftanın Popüler İçerik Tarzı**: En çok tekrar eden içerik temasını belirle.
            2. **Neden Tutuyor?**: Bu akımın psikolojik veya algoritmik nedenini açıkla.
            3. **Altın Örnek**: En yüksek izlenmeye sahip videonun linkini ve kullanılan gerçek müzik adını yaz.
            4. **Uygulanabilir 3 Taktik**: İçerik üreticilerinin bu trendi kendi nişlerine nasıl uyarlayabileceğini yaz.
            """
            
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=analiz_prompt
            )
            
            if response and response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("✅ Gemini 3 analizi profesyonel formatta tamamladı.")
                
        except Exception as e:
            print(f"❌ Gemini Analiz Hatası: {e}")

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        veri_yakala_ve_analiz_et(key)
    else:
        print("Hata: GEMINI_API_KEY bulunamadı!")
