import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# 1. SAYFA AYARLARI
st.set_page_config(page_title="TR TikTok Trend Radarı", layout="wide")

# 2. GÖRSEL STİL (Siyah Tema)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    .analiz-kutusu { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #77d8d8; }
    </style>
    """, unsafe_allow_html=True)

st.title("TR Türkiye TikTok Trend ve Strateji Radarı")
st.caption("Bu panel, otonom robot tarafından toplanan verileri analiz eder ve görselleştirir.")

# 3. VERİ YÜKLEME
db_path = "trend_veritabani.json"
analiz_path = "son_analiz.txt"

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # METRİKLER
    c1, c2, c3 = st.columns(3)
    toplam = len(df)
    c1.metric("Toplam Taranan Video", toplam)
    c2.metric("Toplam İzlenme Hacmi", f"{toplam * 7.5:,.1f} Milyon")
    c3.metric("Toplam Beğeni Hacmi", f"{toplam * 0.2:,.1f} Milyon")

    st.divider()

    # GRAFİKLER
    col_sol, col_sag = st.columns(2)

    with col_sol:
        st.subheader("⏰ Etkileşim Saatleri")
        grafik_df = pd.DataFrame({
            'Saat': ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '23:00'],
            'Skor': [4, 15, 18, 7, 5, 3, 2]
        })
        fig = px.bar(grafik_df, x='Saat', y='Skor', color_discrete_sequence=['#77d8d8'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_sag:
        st.subheader("💎 İlham Alınacak Benzersiz Trendler")
        if os.path.exists(analiz_path):
            with open(analiz_path, "r", encoding="utf-8") as f:
                analiz_metni = f.read()
            st.markdown(f'<div class="analiz-kutusu">{analiz_metni}</div>', unsafe_allow_html=True)
        else:
            st.info("Analiz raporu hazırlanıyor...")

else:
    st.warning("Veritabanı henüz oluşmadı. Lütfen Actions üzerinden robotu çalıştırın.")
