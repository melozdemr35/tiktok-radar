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

def promptu_cikar(dosya_yolu):
    """son_strateji.txt dosyasından sadece AI Promptunu (garantili yolla) çeker."""
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
            
        # 🤖 ve 📝 emojileri arasındaki metni kopar (Format ne kadar bozulursa bozulsun çalışır)
        if "🤖" in icerik and "📝" in icerik:
            ham_prompt = icerik.split("🤖")[1].split("📝")[0]
            # Başlık metnini ve gereksiz > * gibi süsleri temizle
            temiz_prompt = re.sub(r".*PROMPTU.*?:", "", ham_prompt, flags=re.IGNORECASE)
            temiz_prompt = temiz_prompt.replace(">", "").replace("*", "").strip()
            return temiz_prompt
        else:
            print("❌ Hata: Strateji dosyasında '🤖' veya '📝' işaretleri bulunamadı. Metin yapısı farklı.")
            return None
            
    except FileNotFoundError:
        print(f"❌ Hata: {dosya_yolu} bulunamadı.")
        return None

def video_uret_kling(prompt):
    """Kling API'sini kullanarak video üretim emri verir ve sonucu bekler."""
    if not ACCESS_KEY or not SECRET_KEY:
        print("❌ Hata: KLING API anahtarları eksik.")
        return False
        
    print(f"🎬 Kling'e Gönderilen Prompt: {prompt}\n")
    print("⏳ Kling AI videoyu render ediyor... (Bu işlem birkaç dakika sürebilir)")
    
    # 1. JWT Token Oluşturma (Güvenlik Kapısı)
    payload = {
        "iss": ACCESS_KEY,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
        "nbf": datetime.datetime.utcnow() - datetime.timedelta(seconds=5)
    }
    
    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        print(f"❌ JWT Token oluşturulamadı: {e}")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    api_url_task = "https://api.klingai.com/v1/videos/text2video"
    
    data = {
        "prompt": prompt,
        "ratio": "9:16",
        "duration": "5"
    }

    # 1. Görev Başlat
    try:
        response = requests.post(api_url_task, headers=headers, json=data)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("code") == 0:
            task_id = response_data["data"]["task_id"]
            print(f"✅ Video görevi başlatıldı! Görev ID: {task_id}")
        else:
            print(f"❌ API Hatası (Görev Başlatılamadı): {response_data}")
            return False
            
    except Exception as e:
         print(f"❌ İstek Hatası: {e}")
         return False

    # 2. Sonucu Bekle (Polling)
    api_url_result = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
    
    while True:
        try:
            res = requests.get(api_url_result, headers=headers)
            res_data = res.json()
            
            status = res_data.get("data", {}).get("task_status")
            
            if status == "succeed":
                video_url = res_data["data"]["task_result"]["videos"][0]["url"]
                print(f"🎉 Video Hazır! URL: {video_url}")
                
                print("📥 Video indiriliyor...")
                video_icerik = requests.get(video_url).content
                with open("video_output.mp4", "wb") as f:
                    f.write(video_icerik)
                print("✅ Video başarıyla kaydedildi: video_output.mp4")
                return True
                
            elif status == "failed":
                print("❌ Video üretimi başarısız oldu (Kling reddetti).")
                return False
                
            else:
                print("⏳ İşleniyor... Kling videoyu çiziyor (30 saniye bekleniyor)")
                time.sleep(30)
                
        except Exception as e:
            print(f"❌ Durum kontrolü sırasında hata: {e}")
            time.sleep(30)

if __name__ == "__main__":
    hedef_prompt = promptu_cikar(STRATEJI_DOSYASI)
    if hedef_prompt:
        video_uret_kling(hedef_prompt)
