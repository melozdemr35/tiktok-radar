import os
import time
import multiprocessing
from datetime import datetime
from tiktok_uploader.upload import upload_video
from playwright.sync_api import Locator

# --- 🛰️ MODAL KATİLİ (DÖNGÜSÜZ VERSİYON) ---
# Orijinal tıklama fonksiyonunu güvenli bir yere saklıyoruz
orijinal_click = Locator.click

def modal_katili_yama(video_no):
    def yeni_click(self, *args, **kwargs):
        kwargs['force'] = True
        
        # 🛡️ DÖNGÜYÜ KIRAN MANTIK: 
        # Eğer zaten "Turn on" butonuna basmaya çalışıyorsak, tekrar kontrol etme!
        is_modal_button = "Turn on" in str(args) or kwargs.get("name") == "Turn on"
        
        if not is_modal_button:
            try:
                # Sadece ana işlemler sırasında modal kontrolü yap
                turn_on_button = self.page.get_by_role("button", name="Turn on")
                if turn_on_button.is_visible():
                    print(f"🎯 Modal yakalandı, onaylanıyor...")
                    # DİKKAT: Burada 'orijinal_click' kullanıyoruz ki döngüye girmesin!
                    orijinal_click(turn_on_button, force=True)
                    time.sleep(2)
            except:
                pass

        # Fotoğraf al ve orijinal tıklamayı yap
        dosya_adi = f"adim_{video_no}_{int(time.time())}.png"
        try:
            self.page.screenshot(path=dosya_adi)
        except:
            pass
            
        return orijinal_click(self, *args, **kwargs)
    
    # Yamayı sisteme entegre et
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
                if "📝" in satir and ":" in satir: aciklama = satir.split(":", 1)[-1]
                if "🏷️" in satir and ":" in satir: etiketler = satir.split(":", 1)[-1]
            if aciklama and etiketler:
                bilgiler.append(f"{aciklama.strip()}\n\n{etiketler.strip()}")
        return bilgiler
    except: return []

def yukleme_islemcisi(video_yolu, metin, video_no):
    modal_katili_yama(video_no) # Yamayı yükle
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not COOKIES_TXT_ICERIK:
        print(f"❌ HATA: Çerez dosyası bulunamadı!")
        return

    cookie_path = os.path.abspath(f"tiktok_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)

    try:
        # TikTok sisteminin oturması için 10 saniye ön hazırlık
        upload_video(
            os.path.abspath(video_yolu),
            description=metin,
            cookies=cookie_path, 
            headless=False 
        )
        print(f"✅ {video_no}. İŞLEM BAŞARIYLA TAMAMLANDI!")
        
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
                p = multiprocessing.Process(target=yukleme_islemcisi, args=(video_adi, paylasimlar[i-1], i))
                p.start()
                p.join()
                print("☕ Güvenlik molası...")
                time.sleep(20)
