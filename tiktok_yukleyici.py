import os
import re
import json
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan anahtarları al (Boşlukları otomatik temizle)
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID", "").strip()
TIKTOK_COOKIES = os.environ.get("TIKTOK_COOKIES", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Metinleri ayıklar."""
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
    """Hibrit yöntem: Önce tam seti, olmazsa tekil ID'yi dener."""
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    # Kurabiye dosyasını oluştur
    cookie_path = os.path.abspath(f"final_cookie_{video_no}.json")
    
    try:
        # 1. ÖNCELİK: TIKTOK_COOKIES (Tam JSON seti)
        if TIKTOK_COOKIES and TIKTOK_COOKIES.startswith("["):
            with open(cookie_path, 'w', encoding='utf-8') as f:
                f.write(TIKTOK_COOKIES)
            print("📦 Tam çerez seti (JSON) kullanılıyor.")
        
        # 2. ÖNCELİK: SESSION_ID (Eğer tam set yoksa veya hatalıysa)
        elif session_id:
            simple_cookies = [{"name": "sessionid", "value": session_id, "domain": ".tiktok.com", "path": "/"}]
            with open(cookie_path, 'w', encoding='utf-8') as f:
                json.dump(simple_cookies, f)
            print("🔑 Tekil SessionID üzerinden dosya oluşturuldu.")
        
        else:
            print("❌ HATA: Hiçbir kimlik bilgisi (Secret) bulunamadı!")
            return

        video_abs_path = os.path.abspath(video_yolu)
        
        # 🎯 YÜKLEME DENEMESİ
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA YÜKLENDİ!")
        
    except Exception as e:
        print(f"❌ {video_no}. Yükleme sırasında bir engel çıktı: {e}")
    finally:
        if os.path.exists(cookie_path): os.remove(cookie_path)

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    if not paylasimlar:
        print("📭 Veri yok.")
    else:
        bugun = datetime.now().strftime("%d-%m")
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                # Her yükleme için taptaze bir işlem (process)
                p = multiprocessing.Process(target=yukleme_islemcisi, args=(video_adi, paylasimlar[i-1], SESSION_ID, i))
                p.start()
                p.join()
                time.sleep(15) # TikTok için güvenlik beklemesi
