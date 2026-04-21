import os
import time
import requests
import re
import jwt
import datetime

# GitHub Secrets'tan anahtarları çek
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
    
    # 🔊 SES VE FORMAT HİLESİ: Promptun sonuna ses komutlarını biz ekliyoruz
    gucendirilmis_prompt = f"{prompt}. Cinematic sound effects, atmospheric background audio, high quality synchronized sound, 9:16 vertical orientation."

    print(f"\n🚀 {video_no}. VİDEO ÜRETİLİYOR (9:16 Dikey & Sesli Mod)...")
    
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
        "ratio": "9:16",
        "duration": "10",
        "mode": "pro", # Ses ve kalite için 'pro' şart
        "cfg_scale": 0.5
    }

    try:
        api_url_task = "https://api.klingai.com/v1/videos/text2video"
        response = requests.post(api_url_task, headers=headers, json=data)
        task_id = response.json()["data"]["task_id"]
        
        api_url_result = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
        while True:
            res_data = requests.get(api_url_result, headers=headers).json()
            status = res_data.get("data", {}).get("task_status")
            
            if status == "succeed":
                video_url = res_data["data"]["task_result"]["videos"][0]["url"]
                bugun = datetime.datetime.now().strftime("%d-%m")
                dosya_adi = f"video_{bugun}_{video_no}.mp4"
                
                video_icerik = requests.get(video_url).content
                with open(dosya_adi, "wb") as f:
                    f.write(video_icerik)
                print(f"✅ Dikey ve Sesli Video Hazır: {dosya_adi}")
                return True
            elif status == "failed": return False
            else:
                print(f"⏳ {video_no}. Video Hazırlanıyor... ({status})")
                time.sleep(60)
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    promp_listesi = promptlari_ayikla(STRATEJI_DOSYASI)
    if promp_listesi:
        for index, p in enumerate(promp_listesi[:2]):
            video_uret_kling(p, index + 1)
            time.sleep(15)
