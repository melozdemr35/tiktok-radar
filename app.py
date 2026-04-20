import streamlit as st
import pandas as pd
import json
import os
import re
import plotly.express as px

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="TR TikTok Trend Radarı", layout="wide")

# 2. GÖRSEL STİL
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    .analiz-kutusu { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #77d8d8; }
    .stTable { background-color: #1e2130; color: white; }
    </style>
    """, unsafe_allow_html=True)

def parse_number(val):
    if pd.isna(val): return 0
    val_str = str(val).upper().replace(',', '.').strip()
    multiplier = 1
    if 'M' in val_str: multiplier = 1_000_000
    elif 'K' in val_str: multiplier = 1_000
    num_match = re.search(r'[\d\.]+', val_str)
    if num_match:
        try: return float(num_match.group()) * multiplier
        except: return 0
    return 0

def format_milyon(val):
    if val >= 1_000_000: return f"{val / 1_000_000:.1f} Milyon"
    elif val >= 1_000: return f"{val / 1_000:.1f} Bin"
    return f"{val:,.0f}"

def concept_detect(text):
    text = str(text).lower()
    if "pov" in text: return "POV"
    if any(x in text for x in ["röportaj", "sorduk"]): return "Röportaj"
    if "edit" in text: return "Edit"
    return "Genel"

st.title("TR Türkiye TikTok Trend ve Strateji Radarı")
st.caption("Otonom robot verileri analiz ediliyor. Yabancı sızıntılar temizlenmiştir.")

db_path = "trend_veritabani.json"
analiz_path = "son_analiz.txt"

if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    if df.empty:
        st.warning("⏳ Radar şu an taze verileri topluyor... Lütfen birazdan sayfayı yenileyin.")
        st.stop()
        
    df['n_likes'] = df['likes'].apply(parse_number)
    df['n_comments'] = df['comments'].apply(parse_number)
    df['İçerik Türü'] = df['desc'].apply(concept_detect)

    # 🛡️ YENİ: AKILLI KARA LİSTE (Suçluluğu kanıtlanana kadar herkes masumdur) 🛡️
    def akilli_filtre(row):
        metin = f" {str(row.get('desc', ''))} ".lower()
        etiketler = [str(t).lower().replace('#', '') for t in row.get('hashtags', [])]
        
        # Sadece KESİN yabancı kelimeleri yakala (Boşluklara dikkat ki kelime içlerini kesmesin)
        kara_liste_kelimeler = [
            " the ", " and ", " you ", " for ", " is ", " this ", " that ", " my ", " with ",
            " wedding ", " daughter ", " toddler ", " cheese ", " defendia "
        ]
        
        # Etiketlerdeki kesin yabancı izler (Not: fyp ve viral'i ellemiyoruz, Türkler de çok kullanıyor!)
        kara_liste_etiket = ["parati", "foryoupage", "wedding", "toddler", "xyzbca"]
        
        # Eğer metinde kara liste kelimesi varsa -> SİL
        if any(k in metin for k in kara_liste_kelimeler):
            return False
            
        # Eğer etiketlerde kesin yabancı etiket varsa -> SİL
        if any(e in kara_liste_etiket for e in etiketler):
            return False
            
        # Kalan her şey (Sadece emoji atanlar, hiçbir şey yazmayanlar, Türkler) EKRANA ÇIKAR!
        return True
    
    # Filtreyi uygula
    df = df[df.apply(akilli_filtre, axis=1)]

    if df.empty:
        st.error("🚨 Filtre sonrası veri kalmadı. Otonom robotun yeni hasat yapmasını bekleyin.")
        st.stop()


    # --- ÜST METRİKLER ---
    col1, col2, col3 = st.columns(3)
    toplam_video = len(df)
    toplam_begeni = df['n_likes'].sum()
    
    col1.metric("Toplam Taranan Yerel Video", toplam_video)
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

    st.divider()

    # --- TOP 10 TÜRKİYE ARENASI ---
    st.subheader("🇹🇷 Türkiye Etkileşim Arenası (Top 10 Yerel)")

    if not df.empty:
        top_10_tr = df.sort_values(by='n_likes', ascending=False).head(10)
        st.dataframe(
            top_10_tr[['desc', 'İçerik Türü', 'likes', 'comments', 'link']],
            column_config={
                "link": st.column_config.LinkColumn("Videoyu İzle", display_text="🔗 TR Videoyu Aç"),
                "likes": "❤️ Beğeni",
                "comments": "💬 Yorum",
                "desc": "Videonun Açıklaması"
            },
            use_container_width=True, hide_index=True
        )

    st.divider()

    # --- ALT PANEL ---
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
