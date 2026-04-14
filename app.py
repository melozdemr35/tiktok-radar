import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import google.generativeai as genai

# --- SAYI FORMATLAMA FONKSİYONU ---
def format_sayi(num):
    try:
        n = float(num)
        if n >= 1_000_000: return f"{n / 1_000_000:.1f}M"
        if n >= 1_000: return f"{n / 1_000:.1f}K"
        return str(int(n))
    except: return "0"

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TikTok Trend Radarı PRO", page_icon="🚀", layout="wide")

# Veritabanını Yükle
@st.cache_data
def veri_yukle():
    try:
        with open("trend_veritabani.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

tum_veriler = veri_yukle()

# --- SOL MENÜ: KONTROL MERKEZİ ---
st.sidebar.title("🛠️ Kontrol Merkezi")
st.sidebar.markdown("---")

zaman_filtresi = st.sidebar.selectbox(
    "Analiz Zaman Aralığı:",
    ["Tüm Zamanlar", "Son 24 Saat", "Son 3 Gün", "Son 7 Gün"]
)

simdi = datetime.now()
veriler = []

for v in tum_veriler:
    try:
        video_tarihi = datetime.fromisoformat(v['tarih'])
        fark = simdi - video_tarihi
        if zaman_filtresi == "Son 24 Saat" and fark.total_seconds() <= 86400: veriler.append(v)
        elif zaman_filtresi == "Son 3 Gün" and fark.days <= 3: veriler.append(v)
        elif zaman_filtresi == "Son 7 Gün" and fark.days <= 7: veriler.append(v)
        elif zaman_filtresi == "Tüm Zamanlar": veriler.append(v)
    except:
        if zaman_filtresi == "Tüm Zamanlar": veriler.append(v)

st.sidebar.markdown("---")

st.sidebar.subheader("🤖 Gemini Strateji Asistanı")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if st.sidebar.button("✨ Trendleri Analiz Et & Fikir Üret"):
    if not api_key:
        st.sidebar.error("Lütfen API anahtarınızı girin.")
    elif len(veriler) < 3:
        st.sidebar.warning("Analiz için yeterli veri yok.")
    else:
        with st.spinner("Uygun yapay zeka modeli aranıyor ve analiz ediliyor..."):
            try:
                genai.configure(api_key=api_key)
                
                # --- KRİTİK: OTOMATİK MODEL SEÇİCİ ---
                # API Key'in desteklediği tüm modelleri listele
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Tercih sıramız (En yeni olandan eskiye doğru)
                targets = [
                    'models/gemini-1.5-flash-latest', 
                    'models/gemini-1.5-flash', 
                    'models/gemini-1.5-pro', 
                    'models/gemini-pro'
                ]
                
                selected_model = None
                for t in targets:
                    if t in available_models:
                        selected_model = t
                        break
                
                # Eğer listede yoksa bile ilk bulduğun çalışan modeli seç
                if not selected_model and available_models:
                    selected_model = available_models[0]
                
                if not selected_model:
                    st.sidebar.error("Hesabınızda uygun model bulunamadı.")
                else:
                    model = genai.GenerativeModel(selected_model)
                    
                    # Veriyi hazırla
                    ozet_metin = ""
                    top_15 = sorted(veriler, key=lambda x: x.get('izlenme', 0), reverse=True)[:15]
                    for v in top_15:
                        ozet_metin += f"- Açıklama: {v.get('desc')} | Hashtagler: {v.get('hashtagler')}\n"
                    
                    prompt = f"""
                    Sen profesyonel bir TikTok stratejistisin. Türkiye verileri şunlar:
                    {ozet_metin}
                    Lütfen:
                    1. Şu anki ana konsepti (mizah, edit, POV vb.) açıkla.
                    2. Bu trendleri kullanarak çekebileceğim 3 adet yaratıcı içerik fikri ver.
                    3. Neden viral olabileceğini açıkla.
                    """
                    
                    response = model.generate_content(prompt)
                    st.session_state['ai_analiz'] = response.text
                    st.sidebar.success(f"Analiz Tamamlandı! (Kullanılan: {selected_model})")
            except Exception as e:
                st.sidebar.error(f"Hata detayı: {e}")

# --- ANA PANEL ---
st.title(f"📈 Türkiye TikTok Trend Radarı")

if 'ai_analiz' in st.session_state:
    with st.expander("✨ GEMINI YAPAY ZEKA STRATEJİ RAPORU", expanded=True):
        st.markdown(st.session_state['ai_analiz'])

if not veriler:
    st.warning("Gösterilecek veri yok.")
else:
    # Metrikler
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Analiz Edilen", len(veriler))
    m2.metric("İzlenme", format_sayi(sum(v.get('izlenme', 0) for v in veriler)))
    m3.metric("Beğeni", format_sayi(sum(v.get('begeni', 0) for v in veriler)))
    m4.metric("Yorum", format_sayi(sum(v.get('yorum', 0) for v in veriler)))
    st.divider()

    # Grafikler
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader("⏰ Altın Paylaşım Saatleri")
        saatler = {i: {"izl": 0, "beg": 0, "adet": 0} for i in range(24)}
        for v in veriler:
            try:
                h = datetime.fromisoformat(v['tarih']).hour
                saatler[h]["izl"] += v.get('izlenme', 0); saatler[h]["beg"] += v.get('begeni', 0); saatler[h]["adet"] += 1
            except: pass
        saat_list = [{"Saat": f"{h:02d}:00", "Güç": round((s["beg"]/s["izl"]*100),2)} for h,s in saatler.items() if s["izl"] > 0]
        if saat_list: 
            df_s = pd.DataFrame(saat_list).sort_values("Güç", ascending=False).head(7)
            st.bar_chart(df_s.set_index("Saat"))

    with row1_col2:
        st.subheader("🎵 Popüler Trend Sesler")
        muzikler = [v.get('muzik') for v in veriler if v.get('muzik')]
        if muzikler:
            df_m = pd.DataFrame(Counter(muzikler).most_common(5), columns=["Ses Adı", "Kullanım"])
            st.table(df_m)

    st.divider()
    st.subheader("💎 İncelenmesi Gereken Viral Trendler")
    sirali = sorted(veriler, key=lambda x: (x.get('begeni', 0)/x.get('izlenme', 1) if x.get('izlenme', 0)>5000 else 0), reverse=True)[:5]
    for i, v in enumerate(sirali, 1):
        st.markdown(f"**{i}.** [Videoya Git]({v['url']}) | ❤️ Beğeni: {format_sayi(v.get('begeni'))} | 💬 Yorum: {format_sayi(v.get('yorum'))}")