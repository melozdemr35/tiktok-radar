import os
import re
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
            aciklama = ""
            etiketler = ""
            
            for satir in satirlar:
                # 📝 emojisi geçen satırı find ve iki noktadan sonrasını al
                if "📝" in satir and ":" in satir:
                    aciklama = satir.split(":", 1)[-1].replace("*", "").strip()
                # 🏷️ emojisi geçen satırı find ve iki noktadan sonrasını al
                if "🏷️" in satir and ":" in satir:
                    etiketler = satir.split(":", 1)[-1].replace("*", "").strip()
            
            if aciklama and etiketler:
                bilgiler.append(f"{aciklama}\n\n{etiketler}")
                print(f"✅ Metin Yakalandı: {aciklama[:40]}...")
            else:
                print("⚠️ Bu blokta gerekli emojiler veya açıklamalar bulunamadı.")

        return bilgiler
    except Exception as e:
        print(f"❌ Dosya ayrıştırma hatası: {e}")
        return []

def tiktok_paylas(video_yolu, metin):
    """Videoyu TikTok'a yükler (Görünmez/Headless Mod)."""
    if not SESSION_ID:
        print("❌ Hata: TIKTOK_SESSION_ID bulunamadı! Secrets kısmını kontrol et.")
        return False

    print(f"🚀 TikTok'a fırlatılıyor: {video_yolu}")
    try:
        # CRITICAL UPDATE: headless=True ekleyerek 'Ekran Yok' hatasını çözüyoruz.
        upload_video(
            video_yolu,
            description=metin,
            cookies={'sessionid': SESSION_ID},
            headless=True # <--- Bu satır GitHub Actions için HAYATİ önem taşıyor.
        )
        print(f"✅ Paylaşım Başarılı: {video_yolu}")
        return True
    except Exception as e:
        print(f"❌ TikTok Yükleme Hatası: {e}")
        print("💡 İPUCU: SessionID eskiyse tarayıcıdan yenisini alıp Secrets'ı güncelle.")
        return False

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 'son_strateji.txt' içinde yüklenecek temiz veri bulunamadı.")
    else:
        # 📅 DOSYA İSMİ İÇİN TARİH (Örn: video_21-04_1.mp4)
        bugun = datetime.now().strftime("%d-%m")
        
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                print(f"📦 {video_adi} yükleme sırasına alındı...")
                tiktok_paylas(video_adi, paylasimlar[i-1])
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
