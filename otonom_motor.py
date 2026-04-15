import google.generativeai as genai
import json
import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def veri_yakala_ve_analiz_et(api_key):
    yeni_videolar = []
    su_an = datetime.now()
    # 10 günlük silme sınırı (Bugün dahil son 10 gün)
    silme_siniri = (su_an - timedelta(days=10)).strftime('%Y-%m-%d')
    
    print(f"[{su_an.strftime('%H:%M:%S')}] TikTok Derin Radar Başlatıldı... (10 Günlük Bellek Aktif)")
    
    try:
        with sync_playwright() as p:
            # Daha gerçekçi tarayıcı başlatma
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale="tr-TR"
            )
            page = context.new_page()
            
            # TikTok Keşfet
            page.goto("https://www.tiktok.com/explore", wait_until="domcontentloaded", timeout=90000)
            print("Sayfa açıldı, elemanların yüklenmesi için 12 saniye bekleniyor...")
            time.sleep(12) 
            
            # --- İNSANSI VE DERİN TARAMA ---
            for i in range(20): 
                page.mouse.wheel(0, 4500)
                time.sleep(3) # TikTok bot koruması için yavaş kaydırma
                if i % 5 == 0:
                    print(f"Tarama Derinliği: %{int(((i+1)/20)*100)}")
            
            # Video elementlerini yakala
            items = page.query_selector_all('div[data-e2e="explore-item"]') or \
                    page.query_selector_all('div[class*="DivItemContainerV2"]')
            
            print(f"Sistemde saptanan potansiyel video sayısı: {len(items)}")

            for item in items:
                try:
                    raw_text = item.inner_text()
                    if not raw_text: continue
                    
                    all_text = raw_text.split('\n')
                    desc_text = all_text[0]
                    
                    music_elem = item.query_selector('h4') or item.query_selector('div[class*="music"]')
                    music_text = music_elem.inner_text() if music_elem else "Popüler Akım"
                    
                    if len(desc_text) > 3:
                        yeni_videolar.append({
                            "desc": desc_text, 
                            "music": music_text,
                            "tarih": su_an.strftime('%Y-%m-%d'),
                            "hashtagler": "Trend Radarı"
                        })
                except: continue
            
            browser.close()
    except Exception as e:
        print(f"Bot Motoru Hatası: {e}")

    # --- VERİTABANI YÖNETİMİ (KORUMALI MOD) ---
    db_path = "trend_veritabani.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            eski_veriler = json.load(f)
    else:
        eski_veriler = []

    # Yeni ve eskileri birleştir
    birlesik_liste = yeni_videolar + eski_veriler
    
    # Boş liste kontrolü
    if birlesik_liste:
        # Sadece 10 gün içindeki verileri tut (Eskileri siler)
        guncel_ve_taze = [v for v in birlesik_liste if v.get("tarih", "2000-01-01") >= silme_siniri]
        
        # Tekilleştirme (Hata korumalı v.get kullanımı)
        son_liste = list({v.get('desc', ''): v for v in guncel_ve_taze if v.get('desc')}.values())

        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(son_liste, f, ensure_ascii=False, indent=4)
        print(f"İşlem Başarılı! {len(yeni_videolar)} yeni eklendi. Toplam aktif kayıt: {len(son_liste)}")
    else:
        print("⚠️ Uyarı: Hiç video yakalanamadı, veritabanı korunuyor.")

    # --- GEMINI ANALİZ (KESİN ÇÖZÜM: 404 FIX) ---
    if api_key and yeni_videolar:
        try:
            genai.configure(api_key=api_key)
            # Model ismini v1beta karmaşasından kurtarmak için sade bıraktık
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            analiz_prompt = f"Aşağıdaki TikTok trendlerini analiz et ve içerik üreticileri için 5 kısa strateji yaz: {str(yeni_videolar[:25])}"
            response = model.generate_content(analiz_prompt)
            
            if response and response.text:
                with open("son_analiz.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("✅ Gemini analizi başarıyla tamamladı.")
            else:
                print("⚠️ Gemini boş yanıt döndürdü.")
        except Exception as e:
            print(f"❌ Gemini Analiz Hatası: {e}")

if __name__ == "__main__":
    # Çevresel değişken kontrolü
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        veri_yakala_ve_analiz_et(key)
    else:
        print("Hata: GEMINI_API_KEY bulunamadı!")
