import streamlit as st
import os

# Sayfa Ayarları
st.set_page_config(page_title="TikTok Radar | Otonom Panel", layout="wide")

# Tasarım (CSS)
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #ffffff; }
    .stButton>button { background-color: #ff3b5c; color: white; border-radius: 20px; width: 100%; }
    .report-box { padding: 20px; border-radius: 15px; background-color: #2d2d2d; border: 1px solid #ff3b5c; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 TikTok Trend Radarı")
st.subheader("7/24 Otonom Analiz Paneli")

# Arka plandaki robotun hazırladığı raporu oku
if os.path.exists("son_analiz.txt"):
    with open("son_analiz.txt", "r", encoding="utf-8") as f:
        analiz_icerigi = f.read()
    
    st.success("✅ Robot en güncel analizi hazırladı!")
    st.markdown("### 🤖 Son Trend Raporu")
    st.markdown(f'<div class="report-box">{analiz_icerigi}</div>', unsafe_allow_html=True)
else:
    st.warning("⏳ Robot henüz ilk raporunu hazırlıyor, lütfen birkaç dakika sonra tekrar kontrol et.")

st.divider()
st.info("💡 Bu rapor her saat başı GitHub robotu tarafından otomatik olarak güncellenir. Bilgisayarını açmana gerek yoktur.")
