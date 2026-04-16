import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px

# 1. SAYFA YAPILANDIRMASI (Orijinal Tasarım Korundu)
st.set_page_config(page_title="TR TikTok Trend Radarı", layout="wide")

# 2. GÖRSEL STİL (Senin Siyah Teman Birebir Aynı)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    .analiz-kutusu { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #77d8d8; }
    .stTable { background-color: #1e2130; color: white; }
    </style>
    """, unsafe_allow_html=True)

# YENİ EKLENTİ: Sayısal Dönüştürücü (13.5M -> 13500000 yapar, sıralamayı düzeltir)
def parse_number(val):
    if not isinstance(val, str): return 0
    val = val.upper().replace(',', '.')
    try:
        if 'M' in val: return float(val.replace('M', '')) * 1_000_000
        if 'K' in val: return float(val.replace('K', '')) * 1_000
        return float(val)
    except: return 0

st.title("TR Türkiye TikTok Trend ve Strateji Radarı")
st.caption("Otonom robot verileri analiz ediliyor. Veriler gerçek etkileşimlere göre sıralanmıştır.")

db_path = "trend_veritabani.json"
analiz_path = "son_analiz.txt"

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # Sayıları sıralama için hazırlıyoruz
    df['n_likes'] = df['likes'].apply(parse_number)
    df['n_comments'] = df['comments'].apply(parse_number)

    # --- ÜST METRİKLER (Orijinal Düzen) ---
    col1, col2, col3 = st.columns(3)
    toplam_video = len(df)
    toplam_begeni = df['n_likes'].sum()
    
    col1.metric("Toplam Taranan Video", toplam_video)
    col2.metric("Toplam Tahmini İzlenme", f"{toplam_begeni * 25:,.0f}") 
    col3.metric("Toplam Beğeni Hacmi", f"{toplam_begeni:,.0f}")

    st.divider()

    # --- ORTA PANEL (Orijinal Düzen) ---
    col_sol, col_sag = st.columns(2)

    with col_sol:
        st.subheader("⏰ Etkileşim Yoğunluk Saatleri")
        saat_ozet = df['kayit_saati'].value_counts().sort_index().reset_index()
        saat_ozet.columns = ['Saat', 'Video Sayısı']
        fig = px.bar(saat_ozet, x='Saat', y='Video Sayısı', color_discrete_sequence=['#77d8d8'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_sag:
        st.subheader("🎵 Şu An Patlayan Gerçek Sesler")
        # DÜZELTME: Artık this/that kelimelerini değil, GERÇEK müzik isimlerini çeker.
        if 'music' in df.columns:
            populer_sesler = df[df['music'] != "Orijinal Ses"]['music'].value_counts().head(5).reset_index()
            populer_sesler.columns = ['Müzik Adı', 'Kullanım']
            if not populer_sesler.empty:
                st.table(populer_sesler)
            else:
                st.info("Şu an popüler bir dış müzik akımı yok, herkes orijinal ses kullanıyor.")
        else:
            st.warning("Müzik verisi henüz işlenmedi.")

    st.divider()

    # --- YENİ EKLENTİ: TOP 10 ETKİLEŞİM ARENASI ---
    st.subheader("🏆 En Yüksek Etkileşimli Top 10 Video (Tıklanabilir)")
    
    top_10 = df.sort_values(by='n_likes', ascending=False).head(10).copy()
    top_10_display = top_10[['desc', 'likes', 'comments', 'link']]
    top_10_display.columns = ['Videonun Açıklaması', 'Beğeni', 'Yorum', 'Video Linki']
    
    st.dataframe(
        top_10_display,
        column_config={
            "Video Linki": st.column_config.LinkColumn("Videoyu İzle", display_text="🔗 TikTok'ta Aç"),
            "Beğeni": st.column_config.TextColumn("❤️ Beğeni"),
            "Yorum": st.column_config.TextColumn("💬 Yorum")
        },
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --- ALT PANEL (Orijinal Düzen) ---
    a1, a2 = st.columns(2)
    with a1:
        st.subheader("🏷️ Popüler Hashtagler")
        all_tags = df['hashtags'].explode().value_counts().head(10).index.tolist()
        st.info(" ".join(all_tags) if all_tags else "#keşfet #fyp #trend")

    with a2:
        st.subheader("💎 Gemini Trend Analizi")
        if os.path.exists(analiz_path):
            with open(analiz_path, "r", encoding="utf-8") as f:
                st.markdown(f'<div class="analiz-kutusu">{f.read()}</div>', unsafe_allow_html=True)
        else:
            st.info("Analiz raporu hazırlanıyor...")

else:
    st.error("⚠️ Veritabanı bulunamadı. Lütfen robotu çalıştırın.")
