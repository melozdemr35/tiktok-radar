import os
import time
import multiprocessing
import re
from datetime import datetime
from tiktok_uploader.upload import upload_video
from playwright.sync_api import Locator

# --- 🛰️ MODAL KATİLİ ---
orijinal_click = Locator.click
_is_busy = False 

def zirve_yamasi(video_no):
    def yeni_click(self, *args, **kwargs):
        global _is_busy
        kwargs['force'] = True 
        if not _is_busy:
            _is_busy = True
            try:
                for btn_name in ["Turn on", "Got it"]:
                    btn = self.page.get_by_role("button", name=btn_name)
                    if btn.count() > 0 and btn.is_visible():
                        print(f"🎯 {video_no}. Video: '{btn_name}' engeli temizleniyor...")
                        orijinal_click(btn, force=True)
                        time.sleep(1.5) 
            except: pass
            finally: _is_busy = False

        try:
            timestamp = int(time.time())
            self.page.screenshot(path=f"adim_{video_no}_{timestamp}.png")
        except: pass
        return orijinal_click(self, *args, **kwargs)
    Locator.click = yeni_click

# --- 🛡️ GÜNLÜK LİMİT KONTROL SİSTEMİ ---
LIMIT_DOSYASI = "gunluk_limit.txt"

def limit_kontrol_et():
    """Bugün 2 video paylaşıldı mı kontrol eder."""
    bugun = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(LIMIT_DOSYASI):
        with open(LIMIT_DOSYASI, "r") as f:
            icerik = f.read().strip()
            if icerik == f"{bugun}_tamam":
                return True
    return False

def limit_kilidi_vur():
    """Görevi tamamlayınca bugünün tarihini kilide yazar."""
    bugun = datetime.now().strftime("%Y-%m-%d")
    with open(LIMIT_DOSYASI, "w") as f:
        f.write(f"{bugun}_tamam")
    print(f"🔒 BUGÜNÜN LİMİTİ DOLDU: {bugun}. Yarın sabah 05:00'e kadar sevkiyat kapalı.")

# -----------------------------------------------------------

COOKIES_TXT_ICERIK = os.environ.get("TIKTOK_COOKIES_TXT", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

def paylasim_saati_geldi_mi(dosya_yolu):
    try:
        if not os.path.exists(dosya_yolu): return True
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        saat_bul = re.search(r"⏰.*?(\d{2}):\d{2}", icerik)
        if saat_bul:
            hedef_saat = saat_bul.group(1)
            su_anki_saat = datetime.now().strftime("%H")
            if hedef_saat == su_anki_saat:
                print(f"✅ Paylaşım saati geldi! (Hedef: {hedef_saat}:00)")
                return True
            else:
                print(f"⏳ Beklemede... Hedef: {hedef_saat}:00 / Şu an: {su_anki_saat}:00")
                return False
        return True
    except: return True

def paylasim_bilgilerini_al(dosya_yolu):
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
                if "📝" in satir and ":" in satir: ac = satir.split(":", 1)[-1].strip().replace("**", "")
                if "🏷️" in satir and ":" in satir: et = satir.split(":", 1)[-1].strip().replace("**", "")
            if ac and et:
                etiket_list = et.split(" ")
                temiz_et = " ".join([f"{e} " for e in etiket_list if e.startswith("#")])
                bilgiler.append(f"{ac}\n\n{temiz_et}")
        return bilgiler
    except: return []

def yukleme_islemcisi(video_yolu, metin, video_no):
    zirve_yamasi(video_no)
    print(f"🚀 {video_no}. Video sevkiyatı başlatıldı...")
    cookie_path = os.path.abspath(f"tiktok_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)
    try:
        upload_video(os.path.abspath(video_yolu), description=metin, cookies=cookie_path, headless=False)
        print(f"✅ {video_no}. VİDEO TİKTOK'A FIRLATILDI!")
        return True
    except Exception as e:
        print(f"⚠️ Hata: {e}")
        return False
    finally:
        if os.path.exists(cookie_path): os.remove(cookie_path)

if __name__ == "__main__":
    # 1. KRİTİK KONTROL: Bugün 2 video zaten atıldı mı?
    if limit_kontrol_et():
        print("💤 Otonom Kurye: Bugün zaten 2 adet video paylaştım. Kredileri korumak için uyuyorum...")
        exit()

    # 2. SAAT KONTROLÜ
    if not paylasim_saati_geldi_mi(STRATEJI_DOSYASI):
        print("🛑 Viral saat bekleniyor...")
    else:
        # 3. YÜKLEME İŞLEMİ
        paylasimlar = paylasim_bilgilerini_al(STRATEJI_DOSYASI)
        if paylasimlar:
            bugun = datetime.now().strftime("%d-%m")
            basarili_sayisi = 0
            for i in range(1, 3):
                video_adi = f"video_{bugun}_{i}.mp4"
                if os.path.exists(video_adi):
                    if yukleme_islemcisi(video_adi, paylasimlar[i-1], i):
                        basarili_sayisi += 1
                        time.sleep(20)
            
            # 4. LİMİT KİLİDİNİ ÇAK
            if basarili_sayisi >= 2:
                limit_kilidi_vur()
