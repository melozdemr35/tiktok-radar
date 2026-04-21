import os
import time
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
    """Kütüphanenin format bug'ını aşmak için klasik Netscape formatını kullanır."""
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not session_id or len(session_id) < 10:
        print(f"❌ HATA: SESSION_ID bulunamadı! Lütfen GitHub Secrets'ı kontrol et.")
        return

    # 🍪 SİHİRLİ DOKUNUŞ: Netscape HTTP Cookie File formatı (.txt)
    # Kütüphanenin json ile kafası karışıyor, bu yüzden en eski ve garantili yolu seçiyoruz.
    cookie_path = os.path.abspath(f"cookies_{video_no}.txt")
    
    # Sekme (\t) boşluklarıyla ayrılmış, tarayıcının mutlak doğru anladığı format
    netscape_icerik = f"# Netscape HTTP Cookie File\n.tiktok.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\t{session_id}\n"
    
    # Text dosyası olarak yazıyoruz
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(netscape_icerik)

    video_abs_path = os.path.abspath(video_yolu)

    try:
        # 🎯 Kütüphanenin en sevdiği şey: İçinde şifre olan bir .txt dosyası
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=True
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA TİKTOK'A YÜKLENDİ!")
        
    except Exception as e:
        print(f"❌ {video_no}. Yükleme sırasında hata: {e}")
        print("💡 İPUCU: Hata devam ediyorsa anahtarın (sessionid) süresi dolmuş demektir.")
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
