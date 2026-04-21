import os
import re
import json
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan tertemiz session id'yi al
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID")
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """🎬, 📝 ve 🏷️ emojilerini takip ederek metni en temiz şekilde ayıklar."""
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

def yukleme_islemcisi(video_yolu, metin, session_id, video_no):
    """Her yüklemeyi izole bir işlem içinde, en garanti kurabiye protokolüyle çalıştırır."""
    print(f"🚀 {video_no}. Video için motor ateşleniyor...")
    
    if not session_id or len(session_id) < 10:
        print(f"❌ {video_no}. Video Hatası: SESSION_ID boş veya eksik!")
        return

    # 🍪 KURABİYE PROTOKOLÜ: Kütüphanenin en kolay okuyacağı format
    cookie_filename = f"temp_cookies_{video_no}.json"
    cookie_path = os.path.abspath(cookie_filename)
    
    cookies = [
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",
            "path": "/"
        }
    ]
    
    with open(cookie_path, 'w') as f:
        json.dump(cookies, f)

    video_abs_path = os.path.abspath(video_yolu)

    try:
        # 🔥 DOĞRUDAN PARAMETRE YÖNTEMİ:
        # Bazı sürümlerde sessionid= session_id olarak da çalışabilir. 
        # Ancak cookies=cookie_path en kararlı yöntemdir.
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO TİKTOK'A FIRLATILDI!")
    except Exception as e:
        print(f"❌ {video_no}. Video Yükleme Hatası: {e}")
        print("💡 İPUCU: Eğer hata 'Redirected' ise SessionID süresi dolmuş veya kopyalarken boşluk kalmış demektir.")
    finally:
        # Temizlik: Geçici dosyayı her ihtimale karşı sil
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 Yüklenecek veri bulunamadı. son_strateji.txt dosyasını kontrol et.")
    else:
        # Tarihli dosya ismini Kling'den gelen formata göre ayarla
        bugun = datetime.now().strftime("%d-%m")
        
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                metin = paylasimlar[i-1]
                
                # İzole process (Asyncio çakışmalarını önler)
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, metin, SESSION_ID, i)
                )
                p.start()
                p.join() # Video bitene kadar bekle
                
                if i < 2:
                    print("☕ TikTok radarına takılmamak için mola veriliyor...")
                    time.sleep(20)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
