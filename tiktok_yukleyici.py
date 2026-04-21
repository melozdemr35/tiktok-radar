import os
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video
from playwright.sync_api import Locator

# --- 🛰️ MODAL KATİLİ & ETKİLEŞİMLİ ETİKET SİSTEMİ ---
orijinal_click = Locator.click
_is_busy = False # Sonsuz döngüyü engelleyen emniyet kilidi

def zirve_yamasi(video_no):
    def yeni_click(self, *args, **kwargs):
        global _is_busy
        kwargs['force'] = True # Kaba kuvvet kilidi her zaman açık
        
        # 🛡️ MODAL TEMİZLİĞİ: Eğer başka bir tık işlemi yapmıyorsak engelleri kontrol et
        if not _is_busy:
            _is_busy = True
            try:
                # TikTok'un önümüze çıkardığı o iki meşhur engel:
                for btn_name in ["Turn on", "Got it"]:
                    btn = self.page.get_by_role("button", name=btn_name)
                    if btn.count() > 0 and btn.is_visible():
                        print(f"🎯 {video_no}. Video: '{btn_name}' engeli yakalandı, temizleniyor...")
                        orijinal_click(btn, force=True)
                        time.sleep(1.5) # Pencerenin kapanması için es
            except:
                pass
            finally:
                _is_busy = False

        # 📸 GÖRSEL RADAR: Her tıklama anını fotoğrafla (Hata takibi için)
        try:
            timestamp = int(time.time())
            self.page.screenshot(path=f"adim_{video_no}_{timestamp}.png")
        except:
            pass
            
        return orijinal_click(self, *args, **kwargs)
    
    # Yamayı Playwright motoruna enjekte ediyoruz
    Locator.click = yeni_click

# -----------------------------------------------------------

COOKIES_TXT_ICERIK = os.environ.get("TIKTOK_COOKIES_TXT", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_bilgilerini_al(dosya_yolu):
    """Metinleri temizler ve etiketleri tıklanabilir (mavi) hale getirmek için boşluk ekler."""
    try:
        if not os.path.exists(dosya_yolu): return []
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        
        video_bloklari = icerik.split("🎬")[1:]
        bilgiler = []
        for blok in video_bloklari:
            satirlar = blok.split('\n')
            ac, et = "", ""
            for satir in satirlar:
                if "📝" in satir and ":" in satir: 
                    ac = satir.split(":", 1)[-1].strip().replace("**", "")
                if "🏷️" in satir and ":" in satir: 
                    et = satir.split(":", 1)[-1].strip().replace("**", "")
            
            if ac and et:
                # 🛠️ ETİKET HİLESİ: Her etiketin sonuna boşluk ekle ki TikTok maviye boyasın
                etiketler_listesi = et.split(" ")
                temiz_etiketler = " ".join([f"{e} " for e in etiketler_listesi if e.startswith("#")])
                bilgiler.append(f"{ac}\n\n{temiz_etiketler}")
        return bilgiler
    except:
        return []

def yukleme_islemcisi(video_yolu, metin, video_no):
    # Radarı ve modal katilini aktif et
    zirve_yamasi(video_no)
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not COOKIES_TXT_ICERIK:
        print(f"❌ HATA: TIKTOK_COOKIES_TXT bulunamadı!")
        return

    cookie_path = os.path.abspath(f"tiktok_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)

    try:
        # 9:16 ve Sesli videoların artık fırlatılma zamanı!
        upload_video(
            os.path.abspath(video_yolu),
            description=metin,
            cookies=cookie_path, 
            headless=False 
        )
        print(f"✅ {video_no}. VİDEO BAŞARIYLA TİKTOK'A YÜKLENDİ!")
        
    except Exception as e:
        print(f"⚠️ {video_no}. Yüklemede bir pürüz çıktı (Resimlere bak): {e}")
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
                print("☕ Güvenlik molası (20 saniye)...")
                time.sleep(20)
