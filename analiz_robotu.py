import google.generativeai as genai
import json
import os

# API Anahtarını GitHub Secrets üzerinden güvenli şekilde alıyoruz
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Hata: API Anahtarı bulunamadı!")
    exit(1)

genai.configure(api_key=api_key)

# 1. Veritabanını oku
try:
    with open("trend_veritabani.json", "r", encoding="utf-8") as f:
        veriler = json.load(f)
except FileNotFoundError:
    print("Veritabanı dosyası bulunamadı!")
    exit(1)

# 2. Analiz için en güncel 15 videoyu seç
top_15 = sorted(veriler, key=lambda x: x.get('izlenme', 0), reverse=True)[:15]
ozet_metin = ""
for v in top_15:
    ozet_metin += f"- {v.get('desc')} | Hashtagler: {v.get('hashtagler')}\n"

# 3. Gemini ile Analiz Yap
model = genai.GenerativeModel('gemini-1.5-flash')
prompt = f"""
Sen profesyonel bir TikTok stratejistisin. Türkiye'deki son trend verileri şunlar:
{ozet_metin}

Lütfen:
1. Şu anki ana konsepti açıkla.
2. 3 adet viral olabilecek içerik fikri ver.
"""

try:
    response = model.generate_content(prompt)
    # 4. Sonucu bir metin dosyasına kaydet
    with open("son_analiz.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Analiz başarıyla tamamlandı ve kaydedildi!")
except Exception as e:
    print(f"Analiz sırasında hata oluştu: {e}")
