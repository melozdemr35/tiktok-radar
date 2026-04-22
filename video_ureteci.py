import os
import time
import requests
import re
import jwt
import datetime
import subprocess

ACCESS_KEY = os.environ.get("KLING_ACCESS_KEY")
SECRET_KEY = os.environ.get("KLING_SECRET_KEY")
STRATEJI_DOSYASI = "son_strateji.txt"

def promptlari_ayikla(dosya_yolu):
    """🤖 PROMPTU ile 🗣️ SESLENDİRME arasındaki görsel komutu cımbızla çeker"""
    try:
        if not os.path.exists(dosya_yolu): return []
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        # Regex güncellemesi: Sadece görsel promptu alır, seslendirme metnine karışmaz
        pattern = r"🤖.*?PROMPTU.*?\:(.*?)(?:🗣️|📝)"
        eslesmeler = re.findall(pattern, icerik, re.DOTALL | re.IGNORECASE)
        return [p.replace("*", "").replace(">", "").strip() for p in eslesmeler if p.strip()]
    except: return []

def video_uret_kling(prompt, video_no):
    if not ACCESS_KEY or not SECRET_KEY: 
        print("❌ Hata: Kling API anahtarları eksik!")
        return None
    
    # 🎥 KRİTİK GÜNCELLEME: Sesi sildik, sadece 9:16 ve 'dudak oynatma' zorluyoruz. 
    # Ses işini Kling yapmayacak, biz FFmpeg ile ekleyeceğiz.
    gucendirilmis_prompt = f"{prompt}. strictly 9:16 vertical orientation, high quality, photorealistic, character is talking to camera, lips moving continuously."

    print(f"\n🚀 {video_no}. VİDEO ÇEKİMİ BAŞLADI (Kling - Dikey Format / Sessiz Çekim)...")
    
    payload = {
        "iss": ACCESS_KEY,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
        "nbf": datetime.datetime.utcnow() - datetime.timedelta(seconds=5)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    data = {
        "model": "kling-v2-5-turbo",
        "prompt": gucendirilmis_prompt,
        "ratio": "9:16", # Kesin dikey!
        "duration": "5",
        "cfg_scale": 0.5
    }

    try:
        res = requests.post("https://api.klingai.com/v1/videos/text2video", headers=headers, json=data)
        task_id = res.json()["data"]["task_id"]
        
        while True:
            res_data = requests.get(f"https://api.klingai.com/v1/videos/text2video/{task_id}", headers=headers).json()
            status = res_data.get("data", {}).get("task_status")
            
            if status == "succeed":
                video_url = res_data["data"]["task_result"]["videos"][0]["url"]
                bugun = datetime.datetime.now().strftime("%d-%m")
                # İlk indirilen video "ham" yani sessiz olacak
                ham_dosya_adi = f"ham_video_{bugun}_{video_no}.mp4"
                
                video_icerik = requests.get(video_url).content
                with open(ham_dosya_adi, "wb") as f:
                    f.write(video_icerik)
                print(f"📥 Ham (Sessiz) Görüntü İndirildi: {ham_dosya_adi}")
                return ham_dosya_adi
            elif status == "failed": 
                print("❌ Kling Render Hatası!")
                return None
            else:
                print(f"⏳ {video_no}. Video Render Alınıyor... ({status})")
                time.sleep(30)
    except Exception as e:
        print(f"❌ Üretim Hatası: {e}")
        return None

def ses_ile_birlestir(sessiz_video, ses_dosyasi, final_video):
    """FFmpeg Montaj Masası: Sesi ve videoyu milisaniyesine kadar üst üste diker."""
    print(f"🛠️ Montaj Odası: Görüntü ({sessiz_video}) + Ses ({ses_dosyasi}) birleştiriliyor...")
    try:
        komut = [
            "ffmpeg", "-y", "-i", sessiz_video, "-i", ses_dosyasi,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", final_video
        ]
        # Montajı yap
        subprocess.run(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"✅ FİNAL VİDEO HAZIR (Sesli, Dikey ve Profesyonel): {final_video}")
        os.remove(sessiz_video) # Ham (sessiz) videoyu çöpe atıyoruz
        return True
    except Exception as e:
        print(f"❌ Montaj sırasında hata oluştu: {e}")
        return False

if __name__ == "__main__":
    promp_listesi = promptlari_ayikla(STRATEJI_DOSYASI)
    bugun = datetime.datetime.now().strftime("%d-%m")
    
    for index, p in enumerate(promp_listesi[:2]):
        video_no = index + 1
        
        # 1. Aşama: Kling'den sessiz (dudak oynatan) videoyu çek
        ham_video_yolu = video_uret_kling(p, video_no)
        
        if ham_video_yolu:
            ses_dosyasi = f"ses_{video_no}.mp3"
            final_video_adi = f"video_{bugun}_{video_no}.mp4"
            
            # 2. Aşama: Ses Stüdyosunun ürettiği sesi videoya dik!
            if os.path.exists(ses_dosyasi):
                ses_ile_birlestir(ham_video_yolu, ses_dosyasi, final_video_adi)
            else:
                print(f"⚠️ {ses_dosyasi} bulunamadı! Video mecburen sessiz kaydedildi.")
                os.rename(ham_video_yolu, final_video_adi)
        
        time.sleep(15)
