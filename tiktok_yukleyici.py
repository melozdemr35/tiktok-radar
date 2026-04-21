import os
import re
from datetime import datetime
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan session id'yi al
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID")
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Dosyadan açıklama ve etiketleri her video için ayrı ayrı çeker."""
    try:
        if not os.path.exists(dosya_yolu):
            print(f"❌ Hata: {dosya_yolu} bulunamadı.")
            return []

        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        
        # Her video bloğunu ayır (Markdown ve normal metin uyumlu regex)
        videolar = re.split(r"🎬\s*VİDEO\s*NO:", icerik)[1:]
        bilgiler = []
        
        for v in videolar:
            # Açıklama ve etiketleri temiz şekilde yakala (Markdown yıldızlarını yok say)
            aciklama = re.search(r"📝\s*\**TIKTOK AÇIKLAMASI:\**(.*)", v, re.IGNORECASE)
            etiketler = re.search(r"🏷️\s*\**ETİKETLER:\**(.*)", v, re.IGNORECASE)
            
            if aciklama and etiketler:
                # Başındaki ve sonundaki boşlukları/yıldızları temizle
                temiz_aciklama = aciklama.group(1).replace("*", "").strip()
                temiz_etiketler = etiketler.group(1).replace("*", "").strip()
                
                tam_metin = f"{temiz_aciklama}\n\n{temiz_etiketler}"
                bilgiler.append(tam_metin)
        return bilgiler
    except Exception as e:
        print(f"❌ Bilgi okuma hatası: {e}")
        return []

def tiktok_paylas(video_yolu, metin):
    """Videoyu TikTok'a yükler."""
    if not SESSION_ID:
        print("❌ Hata: TIKTOK_SESSION_ID bulunamadı! Lütfen GitHub Secrets'ı kontrol et.")
        return False

    print(f"🚀 Yükleniyor: {video_yolu}")
    print(f"📄 Metin: {metin[:50]}...") # Sadece ilk 50 karakteri göster

    try:
        # tiktok-uploader kütüphanesini kullanarak yükleme yap
        # NOT: Headless False yapıldığında tarayıcı açar, GitHub Actions'ta hata verebilir.
        # tiktok-uploader varsayılan olarak headless çalışır.
        upload_video(
            video_yolu,
            description=metin,
            cookies={'sessionid': SESSION_ID}
        )
        print(f"✅ Paylaşım Başarılı: {video_yolu}")
        return True
    except Exception as e:
        print(f"❌ TikTok Yükleme Hatası: {e}")
        print("💡 İPUCU: SessionID süresi dolmuş olabilir. Tarayıcıdan yeni bir sessionid alıp GitHub Secrets'ı güncellemelisin.")
        return False

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 Yüklenecek açıklama/etiket bulunamadı.")
    else:
        # 📅 BUGÜNÜN TARİHİNİ AL
        bugun = datetime.now().strftime("%d-%m")
        
        # Mevcut mp4 dosyalarını tara (Örn: video_21-04_1.mp4, video_21-04_2.mp4)
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                print(f"📦 {video_adi} için paylaşım başlatılıyor...")
                tiktok_paylas(video_adi, paylasimlar[i-1])
            else:
                print(f"⚠️ Dosya eksik: {video_adi} veya açıklaması bulunamadı, atlanıyor.")
