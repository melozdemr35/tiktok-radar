import google.generativeai as genai
import json
import os

def analiz_yap(api_key):
    # API yapılandırması
    genai.configure(api_key=api_key)
    
    # Model ismini en güncel ve kararlı haliyle çağırıyoruz
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Dosya yollarını GitHub sunucusuna göre ayarlıyoruz
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, "trend_veritabani.json")
    
    # 1. Veritabanını oku (Dosya yoksa sistemi durdurma)
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            veriler = json.load(f)
    else:
        veriler = [{"desc": "Veritabanı henüz oluşmadı", "hashtagler": ""}]

    # 2. Gemini'den analiz iste
    prompt = f"Sen bir sosyal medya uzmanısın. Şu TikTok trend verilerini incele ve Türkiye için 3 viral fikir ver: {str(veriler[:15])}"
    
    try:
        # Analizi gerçekleştir
        response = model.generate_content(prompt)
        
        # 3. Sonucu 'son_analiz.txt' olarak kaydet
        analiz_dosyasi = os.path.join(base_path, "son_analiz.txt")
        with open(analiz_dosyasi, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print("Analiz başarıyla tamamlandı ve dosyaya yazıldı.")
        
    except Exception as e:
        print(f"Gemini Analiz Hatası: {e}")

if __name__ == "__main__":
    # GitHub Secrets'dan anahtarı çek
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        analiz_yap(api_key)
    else:
        print("Hata: GEMINI_API_KEY bulunamadı. Lütfen GitHub Settings -> Secrets kısmını kontrol et.")
