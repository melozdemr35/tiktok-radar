from google import genai
import json
import os
from datetime import datetime

# API Anahtarını al
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Hata: API Anahtarı bulunamadı!")
    exit(1)

# YENİ NESİL GOOGLE GENAI İSTEMCİSİ
client = genai.Client(api_key=api_key)

# 1. Veritabanını oku
try:
    with open("trend_veritabani.json", "r", encoding="utf-8") as f:
        veriler = json.load(f)
except FileNotFoundError:
    print("Veritabanı dosyası bulunamadı!")
    exit(1)

# 2. GÜNCEL VERİ SEÇİMİ
bugun_str = datetime.now().strftime("%Y-%m-%d")
taze_veriler = [v for v in veriler if v.get('kayit_tarihi') == bugun_str]

if len(taze_veriler) < 5:
    guncel_set = veriler[-20:]
else:
    guncel_set = taze_veriler

ozet_metin = ""
for v in guncel_set:
    ozet_metin += f"- Açıklama: {v.get('desc')} | Etiketler: {v.get('hashtags', [])}\n"

# 3. Gemini ile Analiz ve Strateji Oluştur
bugun_tam_tarih = datetime.now().strftime("%d %B %Y")

# 🎯 KRİTİK PROMPT GÜNCELLEMESİ (Günlük Limite uygun olarak 2 video istiyoruz)
prompt = f"""
BUGÜNÜN TARİHİ: {bugun_tam_tarih}
Sen profesyonel bir TikTok Viral Stratejistisin. Türkiye (TR) pazarında uzmanlaşmış bir AI'sın.

TÜRKİYE'DEN GELEN TAZE VERİLER:
{ozet_metin}

GÖREV:
1. Verilere bakarak bugün Türkiye'de TikTok'ta en yüksek etkileşim alacak paylaşım saatini belirle (Format: ⏰ PAYLAŞIM SAATİ: 20:00).
2. 'Absürt Viral' konseptimize uygun, hayvanların konuştuğu veya nesnelere kişilik yüklendiği 2 adet video fikri üret.
3. Her fikri mutlaka şu formatta yaz (Formatı bozma):

⏰ PAYLAŞIM SAATİ: [Buraya Saat Yaz]

🎬 Video 1
🤖 PROMPTU: [Kling AI için detaylı İngilizce görsel komut]
📝 AÇIKLAMA: [Türkçe ilgi çekici açıklama]
🏷️ ETİKETLER: [Hashtagler aralarında boşluk bırakılarak yazılmalı]

(Bu formatı Video 2 için de tekrarla)
"""

try:
    print(f"🧠 {bugun_tam_tarih} verileri analiz ediliyor ve strateji oluşturuluyor...")
    
    # YENİ SİSTEM API ÇAĞRISI
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt
    )
    
    # 4. Sonucu "son_strateji.txt" olarak kaydet (Diğer robotlar bu dosyayı okuyacak)
    with open("son_strateji.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    # Yedek analiz dosyası
    with open("son_analiz.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print(f"✅ Strateji ve Fikirler Başarıyla Oluşturuldu! Dosya: son_strateji.txt")
except Exception as e:
    print(f"Analiz sırasında hata oluştu: {e}")
