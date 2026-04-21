import os
import re
import time
import json
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# Sadece saf SESSION_ID'yi alıyoruz
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Metinleri temiz bir şekilde ayıklar."""
    try:
        if not os.path.exists(dosya_yolu): return []
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        video_bloklari = icerik.split("🎬")[1:]
        bilgiler = []
        for blok in video_bloklari:
            satirlar = blok.split('\n')
            aciklama, etiketler = "", ""
            for satir in satirlar:
                if "📝" in satir and ":" in satir: aciklama = satir.split(":", 1)[-1].replace("*", "").strip()
                if "🏷️" in satir and ":" in satir: etiketler = satir.split(":", 1)[-1].replace("*", "").strip()
            if aciklama and etiketler: bilgiler.append(f"{aciklama}\n\n{etiketler}")
        return bilgiler
    except Exception as e:
        print(f"❌ Ayrıştırma hatası: {e}")
        return []

def yukleme_islemcisi(video_yolu, metin, session_id, video_no):
    """Kütüphanenin bug'ını atlatmak için kusursuz çerez dosyasını oluşturur."""
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not session_id or len(session_id) < 10:
        print(f"❌ HATA: SESSION_ID bulunamadı! Lütfen GitHub Secrets'ı kontrol et.")
        return

    # 🍪 İŞTE SİHİRLİ DOKUNUŞ: Tarayıcının reddedemeyeceği format
    cookie_path = os.path.abspath(f"tiktok_cookie_{video_no}.json")
    kusursuz_cerez = [
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",  # Tarayıcı bunu istiyordu
            "path": "/",              # ve bunu
            "url": "https://www.tiktok.com" # İşi garantiye alan URL parametresi
        }
    ]
    
    # Kendi ellerimizle hazırladığımız çerezi dosyaya yazıyoruz
    with open(cookie_path, 'w', encoding='utf-8') as f:
        json.dump(kusursuz_cerez, f)

    video_abs_path = os.path.abspath(video_yolu)

    try:
        # 🔥 Artık sessionid parametresi yerine hazırladığımız kusursuz dosyayı veriyoruz
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA TİKTOK'A YÜKLENDİ!")
        
    except Exception as e:
        print(f"❌ {video_no}. Yükleme sırasında hata: {e}")
    finally:
        # Çöp bırakmıyoruz
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    if not paylasimlar:
        print("📭 Veri yok.")
    else:
        bugun = datetime.now().strftime("%d-%m")
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                # Playwright asyncio çakışmalarını önlemek için process
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, paylasimlar[i-1], SESSION_ID, i)
                )
                p.start()
                p.join()
                
                if i < 2:
                    print("☕ Güvenlik molası (20 saniye)...")
                    time.sleep(20)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
