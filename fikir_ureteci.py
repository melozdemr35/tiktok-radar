import json
import os
from collections import Counter
import google.generativeai as genai
import time

def veritabani_analiz_et(dosya_yolu="trend_veritabani.json"):
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            veriler = json.load(f)
    except FileNotFoundError:
        print("❌ Hata: trend_veritabani.json bulunamadı!")
        return None

    if not veriler:
        print("❌ Hata: Veritabanı boş!")
        return None

    # 1. HAFTANIN ZİRVE SAATİNİ BULMA
    saatler = [v.get("kayit_saati") for v in veriler if v.get("kayit_saati")]
    if saatler:
        zirve_saat = Counter(saatler).most_common(1)[0][0]
    else:
        zirve_saat = "Belirsiz"

    # 2. SAYILARI PARÇALAMA
    def parse_number(num_str):
        if not num_str: return 0
        num_str = str(num_str).upper().replace(',', '.')
        try:
            if 'M' in num_str:
                return float(num_str.replace('M', '')) * 1000000
            elif 'K' in num_str:
                return float(num_str.replace('K', '')) * 1000
            else:
                return float(num_str)
        except:
            return 0

    # 🛡️ DİL VE TEMİZLİK FİLTRESİ
    def turkce_ve_temiz_mi(metin):
        if not metin: return True
        metin_kucuk = metin.lower()
        yabanci_kelimeler = [" the ", " and ", " you ", " for ", " of ", " in ", " is ", " el ", " la ", " de ", " que ", " my "]
        for kelime in yabanci_kelimeler:
            if kelime in f" {metin_kucuk} ":
                return False
        return True

    temizlenmis_veriler = [v for v in veriler if turkce_ve_temiz_mi(v.get("desc", ""))]

    sirali_veriler = sorted(
        temizlenmis_veriler, 
        key=lambda x: parse_number(x.get("views", "0")) + parse_number(x.get("likes", "0")), 
        reverse=True
    )
    top_10 = sirali_veriler[:10]

    top_10_ozet = []
    for i, v in enumerate(top_10):
        top_10_ozet.append(f"{i+1}. Beğeni: {v.get('likes')} | Açıklama: {v.get('desc')}")

    tum_hashtagler = []
    for v in top_10:
        tum_hashtagler.extend(v.get("hashtags", []))
    populer_hashtagler = [h[0] for h in Counter(tum_hashtagler).most_common(5)]

    return zirve_saat, "\n".join(top_10_ozet), ", ".join(populer_hashtagler)

def prompt_olustur(zirve_saat, top_10_metni, hashtagler):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY bulunamadı.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3-flash-preview')

    # 🧠 YENİ NESİL VİRAL YÖNETMEN TALİMATI
    sistem_talimati = f"""
    Sen dünyanın en ünlü TikTok Viral İçerik Tasarımcısısın. Sıradan ve sıkıcı stok videolardan nefret ediyorsun. 
    Amacın; insanların kaydırmayı bırakıp 'Oha bu ne!' diyeceği, absürt, görsel olarak imkansız ve Türk mizahına uygun videolar tasarlamak.

    GÖREV: Aşağıdaki radar verilerini baz alarak, 2 adet ŞOK EDİCİ video fikri üret.
    
    KURALLAR:
    1. ABSÜRTLÜK: İnsan yerine hayvanları konuştur, cansız nesnelere (karpuz, ekmek, bina) kişilik yükle veya imkansız mekanları birleştir.
    2. GÖRSEL ŞOK (HOOK): Videonun ilk karesi mutlaka şaşırtıcı olmalı (Örn: Sarı çizmeli kedi, kaynak yapan papağan).
    3. SES & DİYALOG: Karakterler mutlaka komik, yöresel (şiveli) veya çok derin bir duyguyla (angry, sarcastic, dramatic) TÜRKÇE konuşmalı.
    4. İNGİLİZCE PROMPT: Kling/Sora promptu İngilizce olmalı ama diyaloglar TÜRKÇE kalmalı.

    RADAR VERİLERİ:
    - Zirve Saat: {zirve_saat}
    - Trend Hashtagler: {hashtagler}
    - Top 10 Analizi:
    {top_10_metni}

    FORMAT:
    ---
    🎬 VİDEO NO: (1 veya 2)
    📊 VİRAL ANALİZ: (Bu videonun neden 'patlayacağını' ve görsel şoku açıkla)
    ⏰ HEDEFLENEN SAAT: (Zamanlama)
    🎬 VİDEO KONSEPTİ: (Absürt fikir)
    🤖 AI VİDEO ÜRETİM PROMPTU: (Sora/Kling için İNGİLİZCE detaylı prompt. Ses tonunu ve duygu durumunu belirt.)
    📝 TIKTOK AÇIKLAMASI: (Merak uyandırıcı Türkçe metin)
    🏷️ ETİKETLER: (#ai #viral #komik #çorum vb.)
    ---
    """

    print("🧠 Gemini 'Viral Canavarı' modunda analiz yapıyor...")
    try:
        response = model.generate_content(sistem_talimati)
        print("\n" + "="*60)
        print(response.text)
        print("="*60)
    except Exception as e:
        if "429" in str(e):
            print("⏳ Kota doldu, 60sn sonra tekrar dene.")
        else:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    analiz = veritabani_analiz_et()
    if analiz:
        prompt_olustur(*analiz)
