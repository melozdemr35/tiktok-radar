import os
import re
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
    """Her yüklemeyi izole bir işlem içinde, en direkt parametrelerle çalıştırır."""
    print(f"🚀 {video_no}. Video için motor ateşleniyor...")
    
    # 🔍 Hata Ayıklama: ID'nin yüklendiğinden emin olalım (İlk 5 karakteri basar)
    if not session_id:
        print(f"❌ Hata: SESSION_ID bulunamadı! GitHub Secrets'ı kontrol et.")
        return
    else:
        print(f"🔑 Session ID yüklendi (Karakter Sayısı: {len(session_id)})")

    video_abs_path = os.path.abspath(video_yolu)

    # 🍪 EN SAĞLAM FORMAT: Doğrudan liste olarak gönderiyoruz
    cookies_list = [
        {
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",
            "path": "/"
        }
    ]

    try:
        # 🔥 Dosya yazma işini bıraktık, direkt listeyi veriyoruz.
        # Eğer bu da olmazsa, kütüphanenin beklediği sessionid= parametresini deneriz.
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookies_list, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO TİKTOK'A FIRLATILDI!")
    except Exception as e:
        print(f"❌ {video_no}. Video Yükleme Hatası: {e}")
        print("💡 İPUCU: Eğer hala 'No valid auth' diyorsa, ID kopyalanırken başına 'sessionid=' eklenmiş olabilir, sadece değeri kopyala.")

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
                    args=(video_adi, metin, SESSION_ID, i)
                )
                p.start()
                p.join() 
                
                if i < 2:
                    print("☕ Güvenlik molası (20 saniye)...")
                    time.sleep(20)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
