import os
import re
import json
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan session id'yi al
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID")
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Emojileri takip ederek metni ayıklayan sağlam yöntem."""
    try:
        if not os.path.exists(dosya_yolu):
            print(f"❌ Hata: {dosya_yolu} bulunamadı.")
            return []

        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        
        # 🎬 emojisine göre videoları bloklara ayır
        video_bloklari = icerik.split("🎬")[1:]
        bilgiler = []
        
        for blok in video_bloklari:
            satirlar = blok.split('\n')
            aciklama = ""
            etiketler = ""
            
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

def yukleme_islemcisi(video_yolu, metin, session_id, video_no):
    """
    Her yüklemeyi izole bir işlem içinde çalıştırarak 
    Playwright asyncio çakışmalarını önler.
    """
    print(f"🚀 {video_no}. Video için tarayıcı hazırlanıyor...")
    
    # 🍪 Kurabiye dosyasını tam yol kullanarak oluştur
    cookie_filename = f"temp_cookies_{video_no}.json"
    cookie_path = os.path.abspath(cookie_filename)
    
    cookies = [
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True
        }
    ]
    
    with open(cookie_path, 'w') as f:
        json.dump(cookies, f)

    try:
        # Headless modda ve geçici cookie dosyasıyla yükle
        upload_video(
            video_yolu,
            description=metin,
            cookies=cookie_path,
            headless=True
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA YÜKLENDİ!")
    except Exception as e:
        print(f"❌ {video_no}. Video Yükleme Hatası: {e}")
    finally:
        # Temizlik: Geçici dosyayı sil
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

def tiktok_paylas_yoneticisi(video_yolu, metin, video_no):
    """Yükleme işlemini yeni bir process olarak başlatır ve yönetir."""
    if not SESSION_ID:
        print("❌ Hata: TIKTOK_SESSION_ID bulunamadı!")
        return False

    # Ayrı bir işlem (Process) başlatıyoruz
    p = multiprocessing.Process(
        target=yukleme_islemcisi, 
        args=(video_yolu, metin, SESSION_ID, video_no)
    )
    p.start()
    p.join() # İşlem bitene kadar ana kodu beklet
    return True

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 Yüklenecek veri bulunamadı.")
    else:
        bugun = datetime.now().strftime("%d-%m")
        
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                print(f"📦 {video_adi} paylaşım sırasına alındı...")
                tiktok_paylas_yoneticisi(video_adi, paylasimlar[i-1], i)
                
                # TikTok'un spam filtresine takılmamak için kısa bir mola
                if i < 2:
                    print("☕ Diğer yükleme öncesi 15 saniye bekleniyor...")
                    time.sleep(15)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
