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
    """Her yüklemeyi izole bir işlem içinde, tam protokol kurabiyesiyle çalıştırır."""
    print(f"🚀 {video_no}. Video için tarayıcı fırını ısıtılıyor...")
    
    # 🍪 KRİTİK GÜNCELLEME: Domain/Path hatasını bitiren tam kurabiye protokolü
    cookie_filename = f"temp_cookies_{video_no}.json"
    cookie_path = os.path.abspath(cookie_filename)
    
    cookies = [
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",
            "path": "/",
            "url": "https://www.tiktok.com", # 👈 Playwright için hayati önemde
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }
    ]
    
    with open(cookie_path, 'w') as f:
        json.dump(cookies, f)

    video_abs_path = os.path.abspath(video_yolu)

    try:
        # Headless modda ve hazırladığımız kurabiye dosyasıyla yükle
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO TİKTOK'A FIRLATILDI!")
    except Exception as e:
        print(f"❌ {video_no}. Video Yükleme Hatası: {e}")
        print("💡 İPUCU: Eğer hala 'Redirect' hatası gelirse, SessionID'nin süresi dolmuş demektir. Yeni bir tane alıp GitHub Secrets'ı güncellemelisin.")
    finally:
        # Temizlik: Geçici kurabiye dosyasını imha et
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 Yüklenecek veri bulunamadı. son_strateji.txt dosyasını kontrol et.")
    else:
        # Tarihli dosya ismini belirle (Kling'den gelen format)
        bugun = datetime.now().strftime("%d-%m")
        
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                metin = paylasimlar[i-1]
                
                # İzole process (Playwright asyncio çakışmalarını önlemek için tek yol)
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, metin, SESSION_ID, i)
                )
                p.start()
                p.join() # İşlem bitmeden diğerine geçmez
                
                if i < 2:
                    print("☕ TikTok radarına takılmamak için 20 saniye mola...")
                    time.sleep(20)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
