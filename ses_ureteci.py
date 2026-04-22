import os
import re
import asyncio
import edge_tts

STRATEJI_DOSYASI = "son_strateji.txt"

# 🎤 SES AKTÖRÜ SEÇİMİ (Ahmet: Enerjik/Kalın Erkek, Emel: Kadın Sesi)
# İstersen tr-TR-EmelNeural olarak değiştirebilirsin.
SES_AKTORU = "tr-TR-AhmetNeural" 

async def ses_olustur(metin, dosya_adi):
    print(f"🎙️ Kayıt Başladı: '{metin[:40]}...' -> {dosya_adi}")
    # Sesi oluştur ve mp3 olarak kaydet
    communicate = edge_tts.Communicate(metin, SES_AKTORU)
    await communicate.save(dosya_adi)

def metinleri_cikar():
    if not os.path.exists(STRATEJI_DOSYASI):
        print("❌ Hata: Strateji dosyası (son_strateji.txt) bulunamadı!")
        return []

    with open(STRATEJI_DOSYASI, "r", encoding="utf-8") as f:
        icerik = f.read()

    # '🗣️ SESLENDİRME:' etiketini bul ve yanındaki metni al
    seslendirme_metinleri = re.findall(r"🗣️ SESLENDİRME:\s*(.*)", icerik)
    
    # Metnin içindeki gereksiz Markdown yıldızlarını (*) temizle
    temiz_metinler = [m.replace("**", "").replace("*", "").replace('"', '').strip() for m in seslendirme_metinleri]
    return temiz_metinler

async def stüdyo_islemi():
    print("🎧 Ses Stüdyosu Kapılarını Açtı...")
    metinler = metinleri_cikar()
    
    if not metinler:
        print("⚠️ Seslendirilecek metin bulunamadı. (Gemini henüz senaryo yazmamış olabilir)")
        return

    # Bulunan her metin için bir .mp3 üret
    for i, metin in enumerate(metinler, 1):
        dosya_adi = f"ses_{i}.mp3"
        await ses_olustur(metin, dosya_adi)
    
    print("✅ Tüm seslendirmeler MP3 olarak başarıyla kaydedildi!")

if __name__ == "__main__":
    # Async yapıyı çalıştır
    asyncio.run(stüdyo_islemi())
