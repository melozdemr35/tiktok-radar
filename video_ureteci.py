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
    """🤖 ve 📝 arasındaki fantastik promptları hatasız çeker."""
    try:
        if not os.path.exists(dosya_yolu):
            print(f"❌ Hata: {dosya_yolu} bulunamadı.")
            return []

        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
            
        # 🛡️ GÜÇLENDİRİLMİŞ CIMBIZ: Robot ve Not simgeleri arasını her türlü yakalar
        pattern = r"🤖.*?PROMPTU.*?\:(.*?)📝"
        eslesmeler = re.findall(pattern, icerik, re.DOTALL | re.IGNORECASE)
        
        prompt_listesi = []
        for p in eslesmeler:
            temiz = p.replace("*", "").replace(">", "").strip()
            if temiz:
                prompt_listesi.append(temiz)
        
        return prompt_listesi
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return []

def video_uret_kling(prompt, video_no):
    """Kling V2.5-Turbo Pro kullanarak 15sn sesli video üretir."""
    if not ACCESS_KEY or not SECRET_KEY:
        print("❌ Hata: API Anahtarları eksik.")
        return False
        
    print(f"\n🚀 {video_no}. VİDEO ÜRETİLİYOR (V2.5-Turbo | Pro | 15sn)...")
    
    # 1. JWT Token Oluşturma
    payload = {
        "iss": ACCESS_KEY,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
        "nbf": datetime.datetime.utcnow() - datetime.timedelta(seconds=5)
    }
    
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        print(f"❌ JWT Hatası: {e}")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 🎥 SATIN ALINAN PAKETE UYGUN AYARLAR
    data = {
        "model": "kling-v2-5-turbo",
        "prompt": prompt,
        "ratio": "9:16",
        "duration": "15", # Senin istediğin o uzunluk
        "mode": "pro",    # Fantastik detaylar için en yüksek kalite
        "cfg_scale": 0.5
    }

    try:
        api_url_task = "https://api.klingai.com/v1/videos/text2video"
        response = requests.post(api_url_task, headers=headers, json=data)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("code") == 0:
            task_id = response_data["data"]["task_id"]
            print(f"✅ Görev kuyrukta! ID: {task_id}")
        else:
            print(f"❌ API Hatası: {response_data}")
            return False
            
    except Exception as e:
         print(f"❌ İstek Hatası: {e}")
         return False

    # 3. Sonucu Bekle ve İndir
    api_url_result = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
    while True:
        try:
            res = requests.get(api_url_result, headers=headers)
            res_data = res.json()
            status = res_data.get("data", {}).get("task_status")
            
            if status == "succeed":
                video_url = res_data["data"]["task_result"]["videos"][0]["url"]
                print(f"🎉 Video {video_no} Hazır! İndiriliyor...")
                
                dosya_adi = f"video_{video_no}.mp4"
                video_icerik = requests.get(video_url).content
                with open(dosya_adi, "wb") as f:
                    f.write(video_icerik)
                print(f"✅ Başarıyla Kaydedildi: {dosya_adi}")
                return True
                
            elif status == "failed":
                print(f"❌ Üretim başarısız. Hata Detayı: {res_data}")
                return False
            else:
                print(f"⏳ {video_no}. video ilmek ilmek işleniyor... (60sn bekleniyor)")
                time.sleep(60) # Uzun videolar için bekleme süresini artırdık
                
        except Exception as e:
            print(f"❌ Durum kontrol hatası: {e}")
            time.sleep(30)

if __name__ == "__main__":
    promp_listesi = promptlari_ayikla(STRATEJI_DOSYASI)
    
    if not promp_listesi:
        print("📭 Üretilecek yeni fantastik prompt bulunamadı.")
    else:
        # Satın aldığın paketle günde en az 2 kaliteli video hedefi
        for index, prompt in enumerate(promp_listesi[:2]):
            video_uret_kling(prompt, index + 1)
            if index < 1: # İki video arası kısa mola
                time.sleep(10)
