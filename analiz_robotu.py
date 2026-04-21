import google.generativeai as genai
import json
import os
from datetime import datetime

# API Anahtarını al
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

# 2. GÜNCEL VERİ SEÇİMİ (Tarih Odaklı)
bugun_str = datetime.now().strftime("%Y-%m-%d")
taze_veriler = [v for v in veriler if v.get('kayit_tarihi') == bugun_str]

# Eğer bugün yeterli veri yoksa, en son eklenen 20 videoyu al (Dinamik güncelleme)
if len(taze_veriler) < 5:
    guncel_set = veriler[-20:]
else:
    guncel_set = taze_veriler

ozet_metin = ""
for v in guncel_set:
    # Veri setindeki alan adlarına göre (desc/hashtags) metni oluştur
    ozet_metin += f"- Açıklama: {v.get('desc')} | Etiketler: {v.get('hashtags', [])}\n"

# 3. Gemini ile Analiz Yap
model = genai.GenerativeModel('gemini-1.5-flash')
bugun_tam_tarih = datetime.now().strftime("%d %B %Y")

prompt = f"""
BUGÜNÜN TARİHİ: {bugun_tam_tarih}
Sen profesyonel bir TikTok Viral Stratejistisin. Sadece Türkiye (TR) pazarındaki en son trendlere odaklan.

TÜRKİYE'DEN GELEN TAZE VERİLER:
{ozet_metin}

GÖREV:
1. Sunulan veriler ışığında, {bugun_tam_tarih} tarihli TikTok Türkiye ekosistemine yönelik kapsamlı analiz yap.
2. Şu anki ana konsepti ve insanların neye ilgi gösterdiğini (mizah, kaos, absürtlük vb.) açıkla.
3. Bizim 'Absürt Viral' konseptimize uygun, ŞOK EDİCİ ve İMKANSIZ 3 adet içerik fikri ver. 
   (Not: Hayvanların konuşturulması veya nesnelere kişilik yüklenmesi gibi viral 'hook'lar kullan).

ÖNEMLİ: Analizin başına mutlaka '{bugun_tam_tarih} Tarihli Trend Analizi' başlığını at.
"""

try:
    print(f"🧠 {bugun_tam_tarih} verileri analiz ediliyor...")
    response = model.generate_content(prompt)
    
    # 4. Sonucu kaydet (W modu dosyayı tamamen yeniler)
    with open("son_analiz.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"✅ Analiz başarıyla tamamlandı! Tarih: {bugun_tam_tarih}")
except Exception as e:
    print(f"Analiz sırasında hata oluştu: {e}")
