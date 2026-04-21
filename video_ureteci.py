import os
import time
import requests
import re
import jwt
import datetime

ACCESS_KEY = os.environ.get("KLING_ACCESS_KEY")
SECRET_KEY = os.environ.get("KLING_SECRET_KEY")
STRATEJI_DOSYASI = "son_strateji.txt"

def promptlari_ayikla(dosya_yolu):
    try:
        if not os.path.exists(dosya_yolu): return []
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
        pattern = r"🤖.*?PROMPTU.*?\:(.*?)📝"
        eslesmeler = re.findall(pattern, icerik, re.DOTALL | re.IGNORECASE)
        return [p.replace("*", "").replace(">", "").strip() for p in eslesmeler if p.strip()]
    except: return []

def video_uret_kling(prompt, video_no):
    if not ACCESS_KEY or not SECRET_KEY: return False
    
    # 🔊 KRİTİK GÜNCELLEME: Dikey formatı zorluyoruz ve sesi kesinlikle TÜRKÇE istiyoruz.
    gucendirilmis_prompt = f"{prompt}. 9:16 vertical orientation, high quality synchronized sound, strictly Turkish language audio, clear Turkish voiceover, cinematic background music, trending tiktok style."

    print(f"\n🚀 {video_no}. VİDEO ÜRETİLİYOR (Dikey & Türkçe Sesli Mod)...")
    
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
        "ratio": "9:16", # 9/16 formatı zorunlu
        "duration": "10",
        "mode": "pro", # Ses üretimi için 'pro' mod şart
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
                dosya_adi = f"video_{bugun}_{video_no}.mp4"
                
                video_icerik = requests.get(video_url).content
                with open(dosya_adi, "wb") as f:
                    f.write(video_icerik)
                print(f"✅ Üretim Tamam (9:16 TR Sesli): {dosya_adi}")
                return True
            elif status == "failed": return False
            else:
                print(f"⏳ {video_no}. Video Render Alınıyor... ({status})")
                time.sleep(60)
    except Exception as e:
        print(f"❌ Üretim Hatası: {e}")
        return False

if __name__ == "__main__":
    promp_listesi = promptlari_ayikla(STRATEJI_DOSYASI)
    for index, p in enumerate(promp_listesi[:2]):
        video_uret_kling(p, index + 1)
        time.sleep(15)
