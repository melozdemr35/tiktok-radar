import os
import re
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan session id'yi al
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID")
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Dosyadan açıklama ve etiketleri her video için ayrı ayrı çeker."""
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        
        # Her video bloğunu ayır
        videolar = icerik.split("🎬 VİDEO NO:")[1:]
        bilgiler = []
        
        for v in videolar:
            # Açıklama (📝) ve Etiketleri (🏷️) ayıkla
            aciklama = re.search(r"📝 TIKTOK AÇIKLAMASI:(.*)", v)
            etiketler = re.search(r"🏷️ ETİKETLER:(.*)", v)
            
            if aciklama and etiketler:
                tam_metin = aciklama.group(1).strip() + "\n\n" + etiketler.group(1).strip()
                bilgiler.append(tam_metin)
        return bilgiler
    except Exception as e:
        print(f"❌ Bilgi okuma hatası: {e}")
        return []

def tiktok_paylas(video_yolu, metin):
    """Videoyu TikTok'a yükler."""
    if not SESSION_ID:
        print("❌ Hata: TIKTOK_SESSION_ID bulunamadı!")
        return False

    print(f"🚀 Yükleniyor: {video_yolu}")
    try:
        # tiktok-uploader kütüphanesini kullanarak yükleme yap
        upload_video(
            video_yolu,
            description=metin,
            cookies={'sessionid': SESSION_ID}
        )
        print(f"✅ Paylaşım Başarılı: {video_yolu}")
        return True
    except Exception as e:
        print(f"❌ TikTok Yükleme Hatası: {e}")
        return False

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    # Mevcut mp4 dosyalarını tara (video_1.mp4, video_2.mp4)
    for i in range(1, 3):
        video_adi = f"video_{i}.mp4"
        if os.path.exists(video_adi) and len(paylasimlar) >= i:
            print(f"📦 {video_adi} için paylaşım başlatılıyor...")
            tiktok_paylas(video_adi, paylasimlar[i-1])
        else:
            print(f"⚠️ {video_adi} veya açıklaması bulunamadı, atlanıyor.")
