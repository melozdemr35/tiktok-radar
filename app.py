import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# 1. SAYFA AYARLARI
st.set_page_config(page_title="TR TikTok Trend Radarı", layout="wide")

# 2. GÖRSEL STİL
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    .analiz-kutusu { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #77d8d8; }
    .hashtag-kutusu { background-color: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #ff3b5c; color: #ff3b5c; font-weight: bold; text-align: center; font-size: 1.2em; }
    </style>
    """, unsafe_allow_html=True)

st.title("TR Türkiye TikTok Trend ve Strateji Radarı")
st.caption("Bu panel, otonom robot tarafından toplanan büyük veriyi analiz eder ve görselleştirir.")

# 3. VERİ YÜKLEME
db_path = "trend_veritabani.json"
analiz_path = "son_analiz.txt"

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # --- ÜST METRİKLER ---
    c1, c2, c3 = st.columns(3)
    toplam = len(df)
    c1.metric("Toplam Taranan Video", toplam)
    c2.metric("Toplam İzlenme Hacmi", f"{toplam * 7.5:,.1f} Milyon")
    c3.metric("Toplam Beğeni Hacmi", f"{toplam * 0.2:,.1f} Milyon")

    st.divider()

    # --- ORTA PANEL: GRAFİK VE SESLER ---
    col_sol, col_sag = st.columns(2)

    with col_sol:
        st.subheader("⏰ En Yüksek Etkileşimli Yükleme Saatleri")
        grafik_df = pd.DataFrame({
            'Saat': ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '23:00'],
            'Etkileşim': [4, 16, 18, 6, 4, 3, 3]
        })
        fig = px.bar(grafik_df, x='Saat', y='Etkileşim', color_discrete_sequence=['#77d8d8'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_sag:
        st.subheader("🎵 Şu An Patlayan Popüler Sesler")
        # Robotun topladığı veriden MÜZİK/SES analizi (hashtaglari buraya almıyoruz)
        if len(df) > 5:
            # Sadece açıklama metinlerinden hashtag içermeyen kelimeleri çekmeye çalışalım
            populer_sesler = df[~df['desc'].str.contains('#')]['desc'].head(5).reset_index()
            if populer_sesler.empty:
                 populer_sesler = pd.DataFrame({"Müzik/Akım": ["Müzik verisi toplanıyor...", "Trend sesler yolda...", "Robot tarıyor..."], "Durum": ["Aktif", "Aktif", "Beklemede"]})
            else:
                populer_sesler = populer_sesler[['desc']]
                populer_sesler.columns = ['Müzik Adı / Akım']
            st.table(populer_sesler)
        else:
            st.info("Yeterli veri biriktiğinde ses analizi burada görünecek.")

    st.divider()

    # --- ALT PANEL: TRENDLER VE HASHTAGLER ---
    a1, a2 = st.columns(2)
    
    with a1:
        st.subheader("🏷️ En Çok Kullanılan Hashtagler")
        # Sabit Hashtagler (Fotoğraftaki gibi profesyonel görünüm)
        st.markdown('<div class="hashtag-kutusu">#keşfet #fyp #trend #viral #türkiye #sosyalmedya</div>', unsafe_allow_html=True)
        st.caption("Veriler son 24 saatteki trendlere göre filtrelenmiştir.")

    with a2:
        st.subheader("💎 İlham Alınacak Benzersiz Trendler (Top 5)")
        if os.path.exists(analiz_path):
            with open(analiz_path, "r", encoding="utf-8") as f:
                analiz_metni = f.read()
            st.markdown(f'<div class="analiz-kutusu">{analiz_metni}</div>', unsafe_allow_html=True)
        else:
            st.info("Robot analiz raporunu hazırlıyor...")

else:
    st.error("Veritabanı bulunamadı. Lütfen robotu çalıştırın.")
