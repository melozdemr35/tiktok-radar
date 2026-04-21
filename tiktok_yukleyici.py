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
    """Emojileri takip ederek metni en garanti şekilde ayıklar."""
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
    """Her yüklemeyi izole bir işlem içinde çalıştırarak çakışmaları önler."""
    print(f"🚀 {video_no}. Video için tarayıcı ateşleniyor...")
    
    # Videonun tam yolunu al (GitHub Actions ortamı için daha güvenli)
    video_abs_path = os.path.abspath(video_yolu)
    
    try:
        # 🔥 KRİTİK GÜNCELLEME: sessionid parametresini doğrudan gönderiyoruz.
        # Bu, 'expected str, not dict' hatasını doğrudan çözer.
        upload_video(
            video_abs_path,
            description=metin,
            sessionid=session_id, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA PAYLAŞILDI!")
    except Exception as e:
        print(f"❌ {video_no}. Video Yükleme Hatası: {e}")
        print("💡 İPUCU: Eğer hala hata alıyorsan TIKTOK_SESSION_ID'yi yenilemelisin.")

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 Yüklenecek veri bulunamadı.")
    else:
        # Tarihli dosya ismini belirle (video_21-04_1.mp4 gibi)
        bugun = datetime.now().strftime("%d-%m")
        
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                metin = paylasimlar[i-1]
                
                # Her yüklemeyi ayrı bir 'Process' olarak başlatıyoruz
                # Bu sayede Playwright'ın asyncio döngüsü her seferinde sıfırlanıyor
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, metin, SESSION_ID, i)
                )
                p.start()
                p.join() # Video bitene kadar ana kodu beklet
                
                if i < 2:
                    print("☕ Diğer yükleme öncesi 20 saniye güvenlik molası...")
                    time.sleep(20)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
