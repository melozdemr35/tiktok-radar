import streamlit as st
import pandas as pd
import json
import os
import re
import plotly.express as px
from datetime import datetime

# --- PERFORMANS İÇİN CACHE ---
@st.cache_data
def load_data(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            # Tarih ve Saat birleştirme
            if not df.empty and 'tarih' in df.columns and 'kayit_saati' in df.columns:
                df['datetime'] = pd.to_datetime(df['tarih'] + " " + df['kayit_saati'], errors='coerce')
            return df
    return pd.DataFrame()

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Ultimate TR Trend Radarı v2", layout="wide")

# 2. ÖZEL STİL (Tasarım Odaklı Siyah Tema)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    .stDataFrame { background-color: #1e2130; border-radius: 10px; }
    .akam-box { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #00f2ea; }
    </style>
    """, unsafe_allow_html=True)

# Sayısal Dönüştürücü
def parse_number(val):
    if pd.isna(val): return 0
    val_str = str(val).upper().replace(',', '.').strip()
    multiplier = 1
    if 'M' in val_str: multiplier = 1_000_000
    elif 'K' in val_str: multiplier = 1_000
    num_match = re.search(r'[\d\.]+', val_str)
    return float(num_match.group()) * multiplier if num_match else 0

# --- AKIM TESPİT SİSTEMİ (Yeni!) ---
def concept_detect(text):
    text = str(text).lower()
    if "pov" in text: return "POV / Kurgu"
    if any(x in text for x in ["röportaj", "sorduk", "mikrofon"]): return "Sokak Röportajı"
    if any(x in text for x in ["şaka", "prank", "kamera şakası"]): return "Mizah / Şaka"
    if any(x in text for x in ["edit", "capcut", "alight"]): return "Visual Edit"
    if any(x in text for x in ["tarif", "yemek", "sunum"]): return "Mutfak / Sunum"
    return "Genel İçerik"

st.title("🚀 Ultimate TR TikTok Strateji Paneli v2")
st.caption("TR Kimlikli Robot Verileri. Viral potansiyeli yüksek akımlar ve gerçek zamanlı analiz.")

df = load_data("trend_veritabani.json")

if not df.empty:
    # Arka Plan Hazırlığı
    df['n_likes'] = df['likes'].apply(parse_number)
    df['n_comments'] = df['comments'].apply(parse_number)
    df['concept'] = df['desc'].apply(concept_detect)

    # --- ÜST METRİKLER ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Video", len(df))
    m2.metric("Ort. Beğeni", f"{int(df['n_likes'].mean()):,}")
    m3.metric("En Popüler Akım", df['concept'].mode()[0])
    m4.metric("Aktif TR Hesabı", "✅ Bağlı")

    st.divider()

    # --- ANA ANALİZ PANELİ ---
    col_sol, col_sag = st.columns([2, 1])

    with col_sol:
        st.subheader("🇹🇷 Türkiye Etkileşim Arenası (Top 10)")
        
        # Kesin TR Filtresi (Daha önce konuştuğumuz Akıllı Kara Liste)
        def tr_filtre(row):
            txt = f"{row['desc']} {row['music']}".lower()
            kara_liste = [' the ', ' is ', ' to ', ' you ', ' and ', ' je ', ' ça ']
            if any(k in txt for k in kara_liste): return False
            return any(h in txt for h in "ğüşıöç") or "orijinal ses" in txt

        df_tr = df[df.apply(tr_filtre, axis=1)].copy()
        top_tr = df_tr.sort_values(by='n_likes', ascending=False).head(10)

        st.dataframe(
            top_tr[['desc', 'likes', 'comments', 'link']],
            column_config={
                "link": st.column_config.LinkColumn("İzle", display_text="🔗 Aç"),
                "desc": "Açıklama"
            },
            use_container_width=True, hide_index=True
        )

    with col_sag:
        st.subheader("🧠 Akım Dağılımı")
        akım_fig = px.pie(df, names='concept', hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        akım_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
        st.plotly_chart(akım_fig, use_container_width=True)

    st.divider()

    # --- ZAMAN VE HASHTAG ANALİZİ ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🔥 Son 24 Saatte Yükselenler")
        if 'datetime' in df.columns:
            last_24h = df[df['datetime'] > pd.Timestamp.now() - pd.Timedelta(hours=24)]
            if not last_24h.empty:
                h_tags = last_24h['hashtags'].explode().value_counts().head(8)
                st.bar_chart(h_tags)
            else:
                st.info("Son 24 saatte yeni veri girişi yok.")

    with c2:
        st.subheader("⏰ En İyi Paylaşım Saatleri")
        saat_fig = px.line(df['kayit_saati'].value_counts().sort_index(), markers=True)
        saat_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(saat_fig, use_container_width=True)

else:
    st.warning("Veritabanı henüz boş. Robotu çalıştırdıktan sonra veriler burada görünecek.")
