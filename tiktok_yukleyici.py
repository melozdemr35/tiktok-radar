import os
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# --- 🛰️ KABA KUVVET VE EKRAN GÖRÜNTÜSÜ SİSTEMİ ---
from playwright.sync_api import Locator, Page

def zorla_ve_kaydet(video_no):
    # Orijinal fonksiyonları saklıyoruz
    orijinal_click = Locator.click
    
    def yeni_click(self, *args, **kwargs):
        kwargs['force'] = True
        try:
            return orijinal_click(self, *args, **kwargs)
        except Exception as e:
            # Hata anında ekran görüntüsü al (İşte tasarımcı farkı!)
            self.page.screenshot(path=f"hata_video_{video_no}.png")
            print(f"📸 Hata anında ekran görüntüsü alındı: hata_video_{video_no}.png")
            raise e
            
    Locator.click = yeni_click

# -----------------------------------------------------------

COOKIES_TXT_ICERIK = os.environ.get("TIKTOK_COOKIES_TXT", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
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

def yukleme_islemcisi(video_yolu, metin, video_no):
    # Kaba kuvvet yamamızı bu video için aktif et
    zorla_ve_kaydet(video_no)
    
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not COOKIES_TXT_ICERIK:
        print(f"❌ HATA: TIKTOK_COOKIES_TXT bulunamadı!")
        return

    cookie_path = os.path.abspath(f"tiktok_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)

    video_abs_path = os.path.abspath(video_yolu)

    try:
        # 🎯 NOT: upload_video kütüphanesinin içindeki 'wait' süresini 
        # değiştiremediğimiz için, bu sürümde robotun "hata" dediği anı yakalayacağız.
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=False 
        )
        print(f"✅ {video_no}. İŞLEM DENENDİ! Lütfen profilini kontrol et.")
        
    except Exception as e:
        print(f"❌ {video_no}. Yükleme sırasında bir şeyler ters gitti: {e}")
    finally:
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
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, paylasimlar[i-1], i)
                )
                p.start()
                p.join()
                time.sleep(15)
