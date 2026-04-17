import json
import os
from collections import Counter
import google.generativeai as genai

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

    # 1. HAFTANIN ZİRVE SAATİNİ BULMA (DİNAMİK)
    saatler = [v.get("kayit_saati") for v in veriler if v.get("kayit_saati")]
    if saatler:
        zirve_saat = Counter(saatler).most_common(1)[0][0]
    else:
        zirve_saat = "Belirsiz"

    # 2. TOP 10 VİDEOYU ÇIKARMA (İzlenme, Beğeni ve Yorum toplamına göre)
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

    # Etkileşim gücüne göre sırala (İzlenme + Beğeni + Yorum)
    sirali_veriler = sorted(
        veriler, 
        key=lambda x: parse_number(x.get("views", "0")) + parse_number(x.get("likes", "0")) + parse_number(x.get("comments", "0")), 
        reverse=True
    )
    top_10 = sirali_veriler[:10]

    # Top 10 verilerini formatlama
    top_10_ozet = []
    for i, v in enumerate(top_10):
        views_metni = f"İzlenme: {v.get('views')} | " if "views" in v else ""
        top_10_ozet.append(f"{i+1}. {views_metni}Beğeni: {v.get('likes')} | Yorum: {v.get('comments')} | Müzik: {v.get('music')} | Açıklama: {v.get('desc')}")

    # En çok tekrar eden popüler hashtagleri süzme
    tum_hashtagler = []
    for v in top_10:
        tum_hashtagler.extend(v.get("hashtags", []))
    populer_hashtagler = [h[0] for h in Counter(tum_hashtagler).most_common(5)]

    return zirve_saat, "\n".join(top_10_ozet), ", ".join(populer_hashtagler)

def prompt_olustur(zirve_saat, top_10_metni, hashtagler):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY bulunamadı. Lütfen ortam değişkenlerine ekleyin.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # GEMINI'YE VERİLEN YENİ EMİR: ÖNCE RADAR ANALİZİ YAP, SONRA ÜRET!
    sistem_talimati = f"""
    Sen profesyonel bir TikTok İçerik Stratejisti ve Yapay Zeka Video Yönetmenisin.
    Aşağıda sağlanan 'Top 10 Trend Verileri'ni ve popüler etiketleri dikkatle incele. 
    
    GÖREV 1 (RADAR ANALİZİ): Önce bu verilerdeki genel eğilimi, yükselen nişleri (örneğin: yapay zeka hikayeciliği, komedi, estetik editler vb.) ve kullanıcı davranışlarını analiz et. Tıpkı bir 'TikTok Trend Radarı' paneli gibi bu haftanın genel stratejisini belirle.
    
    GÖREV 2 (ÜRETİM EMRİ): Kendi hayal gücünü kullanma. Yaptığın bu 'Radar Analizi'ni ve listedeki en yüksek etkileşimli Top 10 videonun konseptini/mantığını harmanlayarak YENİ, viral olma potansiyeli çok yüksek, otomatik üretilmeye uygun bir video fikri oluştur.
    
    RADAR VERİLERİ:
    - Haftanın Zirve Paylaşım Saati: {zirve_saat}
    - En Popüler Hashtagler: {hashtagler}
    - Top 10 Video Analizi (İzlenme/Beğeni/Yorum Sıralı):
    {top_10_metni}

    Lütfen bana doğrudan kopyalayıp sistemde kullanabileceğim şu formatta bir çıktı ver:
    ---
    📊 GEMİNİ RADAR ANALİZİ: (Verilerden çıkardığın kısa genel trend ve strateji yorumu)
    ⏰ HEDEFLENEN SAAT: {zirve_saat}
    🎬 VİDEO KONSEPTİ: (Radar analizine ve Top 10 mantığına dayalı net fikir)
    🤖 AI VİDEO ÜRETİM PROMPTU: (Sora/Kling/Luma gibi yapay zekalara verilecek İNGİLİZCE, detaylı, sinematik kamera açıları içeren prompt)
    📝 TIKTOK AÇIKLAMASI: (Top 10'da tutan tarza uygun, etkileşim çekecek Türkçe metin)
    🏷️ ETİKETLER: (Verideki popüler hashtagler ve konseptle uyumlu eklemeler)
    ---
    """

    print("🧠 Gemini radar verilerini analiz ediyor ve promptu hazırlıyor...")
    try:
        response = model.generate_content(sistem_talimati)
        print("\n" + "="*60)
        print("🎯 ÜRETİM EMRİ HAZIR:")
        print("="*60)
        print(response.text)
        print("="*60)
    except Exception as e:
        print(f"❌ Gemini API Hatası: {e}")

if __name__ == "__main__":
    analiz_sonucu = veritabani_analiz_et()
    if analiz_sonucu:
        saat, metin, etiketler = analiz_sonucu
        prompt_olustur(saat, metin, etiketler)
