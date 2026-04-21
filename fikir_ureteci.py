import json
import os
from collections import Counter
import google.generativeai as genai
import time
from datetime import datetime

def veritabani_analiz_et(dosya_yolu="trend_veritabani.json"):
    try:
        if not os.path.exists(dosya_yolu):
            print("❌ Hata: trend_veritabani.json bulunamadı!")
            return None
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            veriler = json.load(f)
    except Exception as e:
        print(f"❌ Veritabanı okuma hatası: {e}")
        return None

    if not veriler:
        print("❌ Hata: Veritabanı boş!")
        return None

    # 1. ZİRVE SAAT ANALİZİ
    saatler = [v.get("kayit_saati") for v in veriler if v.get("kayit_saati")]
    zirve_saat = Counter(saatler).most_common(1)[0][0] if saatler else "19:00"

    # 2. SAYI TEMİZLEME (İzlenme/Beğeni)
    def parse_number(num_str):
        if not num_str: return 0
        num_str = str(num_str).upper().replace(',', '.')
        try:
            if 'M' in num_str: return float(num_str.replace('M', '')) * 1000000
            if 'K' in num_str: return float(num_str.replace('K', '')) * 1000
            return float(num_str)
        except: return 0

    # 3. YABANCI İÇERİK FİLTRESİ
    def turkce_mi(metin):
        if not metin: return True
        metin_kucuk = metin.lower()
        yabanci_kelimeler = [" the ", " and ", " you ", " for ", " of ", " in ", " is ", " el ", " la ", " de ", " que "]
        return not any(kelime in f" {metin_kucuk} " for kelime in yabanci_kelimeler)

    temiz_veriler = [v for v in veriler if turkce_mi(v.get("desc", ""))]
    
    # En çok etkileşim alan 10 video
    sirali = sorted(temiz_veriler, key=lambda x: parse_number(x.get("views", "0")) + parse_number(x.get("likes", "0")), reverse=True)
    top_10 = sirali[:10]

    top_10_ozet = [f"{i+1}. Beğeni: {v.get('likes')} | Açıklama: {v.get('desc')}" for i, v in enumerate(top_10)]
    
    tum_h = []
    for v in top_10: tum_h.extend(v.get("hashtags", []))
    populer_h = ", ".join([h[0] for h in Counter(tum_h).most_common(5)])

    return zirve_saat, "\n".join(top_10_ozet), populer_h

def prompt_olustur(zirve_saat, top_10_metni, hashtagler):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY bulunamadı.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Daha stabil analiz için

    bugun = datetime.now().strftime("%d %B %Y")

    sistem_talimati = f"""
    BUGÜNÜN TARİHİ: {bugun}
    Sen dünyanın en ünlü TikTok Viral İçerik Tasarımcısısın. Sıradan içeriklerden nefret ediyorsun.
    Amacın; insanların kaydırmayı bırakıp 'Oha bu ne!' diyeceği, absürt, görsel olarak imkansız ve Türk mizahına uygun videolar tasarlamak.

    GÖREV: Aşağıdaki radar verilerini baz alarak, 2 adet ŞOK EDİCİ video fikri üret.
    
    KURALLAR:
    1. ABSÜRTLÜK: İnsan yerine hayvanları konuştur, cansız nesnelere kişilik yükle veya imkansız mekanları birleştir (Örn: Çorum leblebisinin Mars'ta kavrulması).
    2. GÖRSEL ŞOK (HOOK): İlk kare mutlaka şaşırtıcı olmalı.
    3. SES & DİYALOG: Karakterler mutlaka komik, yöresel veya duygulu (angry, sarcastic, dramatic) TÜRKÇE konuşmalı.
    4. İNGİLİZCE PROMPT: Kling/Sora promptu İNGİLİZCE olmalı ama diyaloglar tırnak içinde TÜRKÇE kalmalı.

    RADAR VERİLERİ:
    - Zirve Saat: {zirve_saat}
    - Trendler: {hashtagler}
    - Top 10 Analizi:
    {top_10_metni}

    LÜTFEN BU FORMATI KULLAN:
    ---
    🎬 VİDEO NO: (1 veya 2)
    📊 VİRAL ANALİZ: (Neden patlayacağını açıkla)
    ⏰ HEDEFLENEN SAAT: {zirve_saat}
    🎬 VİDEO KONSEPTİ: (Absürt fikir)
    🤖 AI VİDEO ÜRETİM PROMPTU: (Kling için detaylı İngilizce prompt. Duygu durumunu ve Türkçe diyaloğu ekle.)
    📝 TIKTOK AÇIKLAMASI: (Dikkat çekici metin)
    🏷️ ETİKETLER: (#ai #viral #çorum vb.)
    ---
    """

    print(f"🧠 Gemini 'Viral Canavarı' modunda {bugun} analizini yapıyor...")
    
    try:
        response = model.generate_content(sistem_talimati)
        strateji_metni = response.text
        
        # Terminale bas
        print("\n" + "="*60)
        print(strateji_metni)
        print("="*60)
        
        # 💾 DOSYAYA KAYDET (Video üreticinin okuması için)
        with open("son_strateji.txt", "w", encoding="utf-8") as f:
            f.write(strateji_metni)
        print("✅ Fikirler 'son_strateji.txt' dosyasına mühürlendi!")

    except Exception as e:
        if "429" in str(e):
            print("⏳ Kota doldu, 45 saniye bekleniyor...")
            time.sleep(45)
            # Tekrar deneme yapılabilir veya burada kesilebilir
        else:
            print(f"❌ Gemini Hatası: {e}")

if __name__ == "__main__":
    analiz = veritabani_analiz_et()
    if analiz:
        prompt_olustur(*analiz)
