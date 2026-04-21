import os
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# --- 🛰️ EFSANE HACK: KABA KUVVET (FORCE CLICK) YAMASI ---
# Robotun "önümde baloncuk var" diyerek durmasını engeller.
# Üstteki uyarıları yok sayarak direkt "Paylaş" butonuna zorla basar.
from playwright.sync_api import Locator, Page

orijinal_loc_click = Locator.click
orijinal_loc_fill = Locator.fill
orijinal_page_click = Page.click
orijinal_page_fill = Page.fill

def zorla_loc_click(self, *args, **kwargs):
    kwargs['force'] = True # Kaba kuvvet kilidini açar
    return orijinal_loc_click(self, *args, **kwargs)

def zorla_loc_fill(self, *args, **kwargs):
    kwargs['force'] = True
    return orijinal_loc_fill(self, *args, **kwargs)

def zorla_page_click(self, *args, **kwargs):
    kwargs['force'] = True
    return orijinal_page_click(self, *args, **kwargs)

def zorla_page_fill(self, *args, **kwargs):
    kwargs['force'] = True
    return orijinal_page_fill(self, *args, **kwargs)

Locator.click = zorla_loc_click
Locator.fill = zorla_loc_fill
Page.click = zorla_page_click
Page.fill = zorla_page_fill
# -----------------------------------------------------------

# GitHub Secrets'tan tam kimlik dosyasını alıyoruz
COOKIES_TXT_ICERIK = os.environ.get("TIKTOK_COOKIES_TXT", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """🎬, 📝 ve 🏷️ emojilerini takip ederek metni ayıklar."""
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
    # ⏳ Melih, buradaki süreyi 45 saniyeye çıkardım. 
    # TikTok videoyu yükleyip telif kontrolü yaparken robotumuz "Ares sakinliğiyle" bekleyecek.
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    print("⏳ Telif kontrolünün bitmesi ve butonun canlanması için 45 saniye sabrediyoruz...")
    time.sleep(45) 
    
    if not COOKIES_TXT_ICERIK:
        print(f"❌ HATA: TIKTOK_COOKIES_TXT bulunamadı!")
        return

    cookie_path = os.path.abspath(f"tiktok_tam_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)

    video_abs_path = os.path.abspath(video_yolu)

    try:
        # headless=False ve Full HD ekran ile butonlar artık tam yerinde olacak.
        upload_video(
            video_abs_path,
            description=metin,
            cookies=cookie_path, 
            headless=False 
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA TİKTOK'A YÜKLENDİ!")
        
    except Exception as e:
        print(f"❌ {video_no}. Yükleme sırasında hata: {e}")
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
                
                if i < 2:
                    print("☕ Güvenlik molası (30 saniye)...")
                    time.sleep(30)
            else:
                print(f"⚠️ {video_adi} bulunamadı, bu adım atlanıyor.")
