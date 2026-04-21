import os
import time
import multiprocessing
import re
from datetime import datetime
from tiktok_uploader.upload import upload_video
from playwright.sync_api import Locator

# --- 🛰️ MODAL KATİLİ & ETKİLEŞİMLİ ETİKET SİSTEMİ ---
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
                        print(f"🎯 {video_no}. Video: '{btn_name}' engeli yakalandı, temizleniyor...")
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

# -----------------------------------------------------------

COOKIES_TXT_ICERIK = os.environ.get("TIKTOK_COOKIES_TXT", "").strip()
STRATEJI_DOSYASI = "son_strateji.txt"

# --- 🕵️‍♂️ SAAT MUHAFIZI ---
def paylasim_saati_geldi_mi(dosya_yolu):
    """Analiz robotunun 'son_strateji.txt' içine yazdığı saati kontrol eder."""
    try:
        if not os.path.exists(dosya_yolu): return True # Dosya yoksa direkt yükle (Güvenlik)
        
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
            
        # Dosyadaki "⏰ PAYLAŞIM SAATİ: 20:00" formatını arar
        saat_bul = re.search(r"⏰.*?(\d{2}):\d{2}", icerik)
        if saat_bul:
            hedef_saat = saat_bul.group(1) # Örn: "20"
            su_anki_saat = datetime.now().strftime("%H")
            
            if hedef_saat == su_anki_saat:
                print(f"✅ Paylaşım saati geldi! (Hedef: {hedef_saat}:00)")
                return True
            else:
                print(f"⏳ Beklemede... Hedef: {hedef_saat}:00 / Şu an: {su_anki_saat}:00")
                return False
        return True # Saat formatı bulunamazsa hata vermesin, direkt yüklesin
    except Exception as e:
        print(f"⚠️ Saat kontrolü hatası: {e}")
        return True

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
                if "📝" in satir and ":" in satir: 
                    ac = satir.split(":", 1)[-1].strip().replace("**", "")
                if "🏷️" in satir and ":" in satir: 
                    et = satir.split(":", 1)[-1].strip().replace("**", "")
            
            if ac and et:
                etiketler_listesi = et.split(" ")
                temiz_etiketler = " ".join([f"{e} " for e in etiketler_listesi if e.startswith("#")])
                bilgiler.append(f"{ac}\n\n{temiz_etiketler}")
        return bilgiler
    except:
        return []

def yukleme_islemcisi(video_yolu, metin, video_no):
    zirve_yamasi(video_no)
    print(f"🚀 {video_no}. Video işlemi başlatıldı...")
    
    if not COOKIES_TXT_ICERIK:
        print(f"❌ HATA: TIKTOK_COOKIES_TXT bulunamadı!")
        return

    cookie_path = os.path.abspath(f"tiktok_kimlik_{video_no}.txt")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_TXT_ICERIK)

    try:
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
    # 🕵️‍♂️ SİSTEM ÇALIŞMADAN ÖNCE SAATİ KONTROL ET
    if not paylasim_saati_geldi_mi(STRATEJI_DOSYASI):
        print("🛑 Otonom Kurye: Henüz paylaşım saati değil. Uykuya dönülüyor...")
    else:
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
