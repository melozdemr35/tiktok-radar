import os
import re
from datetime import datetime
from tiktok_uploader.upload import upload_video

# GitHub Secrets'tan session id'yi al
SESSION_ID = os.environ.get("TIKTOK_SESSION_ID")
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Dosyadan açıklama ve etiketleri emoji bazlı, Markdown'a dayanıklı şekilde çeker."""
    try:
        if not os.path.exists(dosya_yolu):
            print(f"❌ Hata: {dosya_yolu} bulunamadı.")
            return []

        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        
        # 🎬 emojisine göre videoları böl (Her bloğu ayrı bir video kabul eder)
        videolar = re.split(r"🎬\s*VİDEO\s*NO:", icerik, flags=re.IGNORECASE)[1:]
        bilgiler = []
        
        for v in videolar:
            # 📝 emojisini bul, Markdown yıldızlarını ve boşlukları atla, metni al
            aciklama_match = re.search(r"📝.*?\**(?:TIKTOK AÇIKLAMASI|AÇIKLAMA)\**\s*:(.*)", v, re.IGNORECASE)
            # 🏷️ emojisini bul, Markdown yıldızlarını ve boşlukları atla, metni al
            etiket_match = re.search(r"🏷️.*?\**(?:ETİKETLER|HASHTAGS)\**\s*:(.*)", v, re.IGNORECASE)
            
            if aciklama_match and etiket_match:
                # Metni temizle: Gereksiz yıldızları ve satır başı/sonu boşlukları yok et
                aciklama = aciklama_match.group(1).replace("*", "").strip()
                etiketler = etiket_match.group(1).replace("*", "").strip()
                
                tam_metin = f"{aciklama}\n\n{etiketler}"
                bilgiler.append(tam_metin)
                print(f"✅ Açıklama yakalandı: {aciklama[:40]}...")
            else:
                print("⚠️ Bir blokta açıklama veya etiket formatı yakalanamadı.")

        return bilgiler
    except Exception as e:
        print(f"❌ Bilgi okuma hatası: {e}")
        return []

def tiktok_paylas(video_yolu, metin):
    """Videoyu TikTok'a yükler."""
    if not SESSION_ID:
        print("❌ Hata: TIKTOK_SESSION_ID bulunamadı! GitHub Secrets'ı kontrol et.")
        return False

    print(f"🚀 TikTok'a fırlatılıyor: {video_yolu}")
    try:
        # tiktok-uploader kütüphanesi headless (arka planda) çalışır
        upload_video(
            video_yolu,
            description=metin,
            cookies={'sessionid': SESSION_ID}
        )
        print(f"✅ Paylaşım Başarılı: {video_yolu}")
        return True
    except Exception as e:
        print(f"❌ TikTok Yükleme Hatası: {e}")
        print("💡 İPUCU: SessionID eskiyse tarayıcıdan (EditThisCookie vb.) yenisini alıp güncelle.")
        return False

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    
    if not paylasimlar:
        print("📭 'son_strateji.txt' içinde yüklenecek veri bulunamadı.")
    else:
        # 📅 DOSYA İSMİ İÇİN TARİH (Örn: video_21-04_1.mp4)
        bugun = datetime.now().strftime("%d-%m")
        
        # Üretilen 2 video için döngü
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            
            if os.path.exists(video_adi) and len(paylasimlar) >= i:
                print(f"📦 {video_adi} yükleme sırasına alındı...")
                tiktok_paylas(video_adi, paylasimlar[i-1])
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
