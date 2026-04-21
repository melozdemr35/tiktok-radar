import os
import json
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan bütün çerezleri (JSON formatında) alıyoruz
TIKTOK_COOKIES_JSON = os.environ.get("TIKTOK_COOKIES")
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """🎬, 📝 ve 🏷️ emojilerini takip ederek metni ayıklar."""
    try:
        if not os.path.exists(dosya_yolu):
            print(f"❌ Hata: {dosya_yolu} bulunamadı.")
            return []
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        
        video_bloklari = icerik.split("🎬")[1:]
        bilgiler = []
        for blok in video_bloklari:
            satirlar = blok.split('\n')
            aciklama, etiketler = "", ""
            for satir in satirlar:
                if "📝" in satir and ":" in satir:
                    aciklama = satir.split(":", 1)[-1].replace("*", "").strip()
                if "🏷️" in satir and ":" in satir:
                    etiketler = satir.split(":", 1)[-1].replace("*", "").strip()
            if aciklama and etiketler:
                bilgiler.append(f"{aciklama}\n\n{etiketler}")
                print(f"✅ Metin Yakalandı: {aciklama[:40]}...")
        return bilgiler
    except Exception as e:
        print(f"❌ Dosya ayrıştırma hatası: {e}")
        return []

def yukleme_islemcisi(video_yolu, metin, cookies_json, video_no):
    """Her yüklemeyi izole bir işlem içinde, tam çerez setiyle çalıştırır."""
    print(f"🚀 {video_no}. Video için tam kimlik kontrolü yapılıyor...")
    
    if not cookies_json:
        print(f"❌ Hata: TIKTOK_COOKIES secret bulunamadı!")
        return

    # 🍪 Çerez dosyasını oluştur (Geçici JSON dosyası)
    cookie_path = os.path.abspath(f"full_cookies_{video_no}.json")
    
    try:
        # GitHub'daki metni JSON dosyası olarak kaydediyoruz
        with open(cookie_path, 'w', encoding='utf-8') as f:
            f.write(cookies_json)

        video_abs_path = os.path.abspath(video_yolu)

        # 🎯 Tam donanımlı yükleme başlatılıyor
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO TİKTOK'A FIRLATILDI!")
        
    except Exception as e:
        print(f"❌ {video_no}. Video Yükleme Hatası: {e}")
    finally:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 Yüklenecek veri bulunamadı. son_strateji.txt dosyasını kontrol et.")
    else:
        bugun = datetime.now().strftime("%d-%m")
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                metin = paylasimlar[i-1]
                
                # İzole process (Playwright asyncio çakışmalarını önlemek için)
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, metin, TIKTOK_COOKIES_JSON, i)
                )
                p.start()
                p.join() 
                
                if i < 2:
                    print("☕ Güvenlik molası (20 saniye)...")
                    time.sleep(20)
            else:
                print(f"⚠️ {video_adi} bulunamadı, atlanıyor.")
