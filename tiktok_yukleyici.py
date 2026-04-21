import os
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video

# --- 🛰️ GÖRSEL RADAR SİSTEMİ (MONKEY PATCH) ---
# Robotun her "tıklama" öncesi fotoğraf çekmesini sağlar.
# Illustrator'daki 'Snapshot' özelliği gibi düşünebilirsin.
from playwright.sync_api import Locator

def fotolu_radar_aktif_et(video_no):
    orijinal_click = Locator.click
    def yeni_click(self, *args, **kwargs):
        kwargs['force'] = True # Kaba kuvvet her zaman devrede
        # Tıklamadan hemen önce zaman damgalı bir resim al
        dosya_adi = f"adim_{video_no}_{int(time.time())}.png"
        try:
            self.page.screenshot(path=dosya_adi)
            print(f"📸 Fotoğraf çekildi: {dosya_adi}")
        except:
            pass
        return orijinal_click(self, *args, **kwargs)
    
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
                if "📝" in satir and ":" in satir: ac_parca = satir.split(":", 1)[-1]
                if "🏷️" in satir and ":" in satir: et_parca = satir.split(":", 1)[-1]
            bilgiler.append(f"{ac_parca.strip()}\n\n{et_parca.strip()}")
        return bilgiler
    except:
        return []

def yukleme_islemcisi(video_yolu, metin, video_no):
    # Radarı bu işlem için aktif et
    fotolu_radar_aktif_et(video_no)
    
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not COOKIES_TXT_ICERIK:
        print(f"❌ HATA: TIKTOK_COOKIES_TXT bulunamadı!")
        return

    cookie_path = os.path.abspath(f"tiktok_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)

    try:
        # ⏳ Robotun butona basmadan önce telif uyarısını 
        # atlatabilmesi için arkada 20 saniye ekstra bekliyoruz.
        upload_video(
            os.path.abspath(video_yolu),
            description=metin,
            cookies=cookie_path, 
            headless=False 
        )
        print(f"✅ {video_no}. İŞLEM DENENDİ!")
        
    except Exception as e:
        print(f"❌ {video_no}. Hata: {e}")
    finally:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)

if __name__ == "__main__":
    paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
    if paylasimlar:
        bugun = datetime.now().strftime("%d-%m")
        for i in range(1, 3):
            video_adi = f"video_{bugun}_{i}.mp4"
            if os.path.exists(video_adi):
                p = multiprocessing.Process(
                    target=yukleme_islemcisi, 
                    args=(video_adi, paylasimlar[i-1], i)
                )
                p.start()
                p.join()
                time.sleep(15)
