import streamlit as st
import pandas as pd
import json
import os
import re
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

# Gelişmiş Sayısal Dönüştürücü (Regex Kalkanlı)
def parse_number(val):
    if pd.isna(val): return 0
    # Sayının içindeki gizli boşlukları ve karakterleri temizler
    val_str = str(val).upper().replace(',', '.').strip()
    multiplier = 1
    if 'M' in val_str: multiplier = 1_000_000
    elif 'K' in val_str: multiplier = 1_000
    
    # Sadece sayısal kısmı çek (Regex)
    num_match = re.search(r'[\d\.]+', val_str)
    if num_match:
        try: return float(num_match.group()) * multiplier
        except: return 0
    return 0

# Rakamları Panelde Şık Gösterme Fonksiyonu
def format_milyon(val):
    if val >= 1_000_000: return f"{val / 1_000_000:.1f} Milyon"
    elif val >= 1_000: return f"{val / 1_000:.1f} Bin"
    return f"{val:,.0f}"

st.title("TR Türkiye TikTok Trend ve Strateji Radarı")
st.caption("Otonom robot verileri analiz ediliyor. Veriler gerçek etkileşimlere göre sıralanmıştır.")

db_path = "trend_veritabani.json"
analiz_path = "son_analiz.txt"

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # Sayıları arka planda matematiksel hale getiriyoruz
    df['n_likes'] = df['likes'].apply(parse_number)
    df['n_comments'] = df['comments'].apply(parse_number)

    # --- ÜST METRİKLER ---
    col1, col2, col3 = st.columns(3)
    toplam_video = len(df)
    toplam_begeni = df['n_likes'].sum()
    
    col1.metric("Toplam Taranan Video", toplam_video)
    col2.metric("Toplam Tahmini İzlenme", format_milyon(toplam_begeni * 25)) 
    col3.metric("Toplam Beğeni Hacmi", format_milyon(toplam_begeni))

    st.divider()

    # --- ORTA PANEL ---
    col_sol, col_sag = st.columns(2)

    with col_sol:
        st.subheader("⏰ Etkileşim Yoğunluk Saatleri")
        if 'kayit_saati' in df.columns:
            saat_ozet = df['kayit_saati'].value_counts().sort_index().reset_index()
            saat_ozet.columns = ['Saat', 'Video Sayısı']
            fig = px.bar(saat_ozet, x='Saat', y='Video Sayısı', color_discrete_sequence=['#77d8d8'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)

    with col_sag:
        st.subheader("🎵 Şu An Patlayan Gerçek Sesler")
        if 'music' in df.columns:
            populer_sesler = df[df['music'] != "Orijinal Ses"]['music'].value_counts().head(5).reset_index()
            populer_sesler.columns = ['Müzik Adı', 'Kullanım']
            if not populer_sesler.empty:
                st.table(populer_sesler)
            else:
                st.info("Şu an popüler bir dış müzik akımı yok.")
        else:
            st.warning("Müzik verisi henüz işlenmedi.")

    st.divider()

    # --- TOP 10 ETKİLEŞİM ARENASI (GLOBAL) ---
    st.subheader("🏆 En Yüksek Etkileşimli Top 10 Video (Global)")
    
    # n_likes üzerinden gerçek sıralama yapıyoruz
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

    # --- YENİ EKLENTİ: TOP 10 TÜRKİYE ARENASI (YEREL) ---
    st.subheader("🇹🇷 Türkiye Etkileşim Arenası (Top 10 Yerel)")

    # İstanbul kimliğiyle toplanan videolardan Türkçe harf içerenleri ayıklar (Kısıtlamasız filtre)
    def tr_filtre_genis(row):
        taranacak = f"{str(row['desc'])} {str(row['music'])}".lower()
        return any(h in taranacak for h in "ğüşıöç")

    df_tr = df[df.apply(tr_filtre_genis, axis=1)].copy()

    if not df_tr.empty:
        # Türkiye şampiyonlarını sırala
        top_10_tr = df_tr.sort_values(by='n_likes', ascending=False).head(10)
        
        st.dataframe(
            top_10_tr[['desc', 'likes', 'comments', 'link']],
            column_config={
                "link": st.column_config.LinkColumn("Videoyu İzle", display_text="🔗 TR Videoyu Aç"),
                "likes": "❤️ Beğeni",
                "comments": "💬 Yorum",
                "desc": "Videonun Açıklaması"
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Yerel radar şu an tarama yapıyor... Türkçe karakterli içerikler bulunduğunda burada listelenecek.")

    st.divider()

    # --- ALT PANEL (Hashtagler ve Gemini) ---
    a1, a2 = st.columns(2)
    with a1:
        st.subheader("🏷️ Popüler Hashtagler")
        if 'hashtags' in df.columns:
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
