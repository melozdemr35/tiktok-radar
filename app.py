import streamlit as st
import os

# Sayfa Genişliği ve Başlık
st.set_page_config(page_title="TikTok Radar | Melih Özdemir", layout="wide", page_icon="🚀")

# Modern Karanlık Tema Tasarımı
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #ffffff; }
    .report-card { 
        padding: 25px; 
        border-radius: 15px; 
        background-color: #2d2d2d; 
        border-left: 5px solid #ff3b5c;
        line-height: 1.6;
    }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 TikTok Trend Radarı")
st.subheader("7/24 Otonom Strateji Paneli")

# Rapor Dosyasını Kontrol Et
if os.path.exists("son_analiz.txt"):
    try:
        with open("son_analiz.txt", "r", encoding="utf-8") as f:
            analiz_metni = f.read()
        
        if len(analiz_metni.strip()) > 10:
            st.success("✅ Robot en taze trendleri yakaladı ve analiz etti!")
            st.markdown("### 🤖 Gemini'nin Strateji Önerileri")
            st.markdown(f'<div class="report-card">{analiz_metni}</div>', unsafe_allow_html=True)
            
            st.divider()
            st.caption("💡 Bu analiz her saat başı TikTok Keşfet verileriyle otomatik olarak güncellenir.")
        else:
            st.warning("⏳ Robot şu an verileri işliyor, rapor birkaç saniye içinde burada olacak...")
            
    except Exception as e:
        st.error(f"Rapor okunurken bir teknik hata oluştu: {e}")
else:
    # Dosya hiç yoksa gösterilecek mesaj
    st.info("👋 Selam Melih! Robot henüz ilk devriyesini tamamlamadı. Yaklaşık 2-3 dakika içinde ilk rapor buraya düşecek.")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueGZ4bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TQvjWWLBVIHiSg8/giphy.gif", width=400)

# Alt Bilgi
st.sidebar.markdown("### 📊 Sistem Durumu")
st.sidebar.write("✅ Otomasyon: Aktif")
st.sidebar.write("✅ Veri Kaynağı: TikTok Keşfet")
st.sidebar.write(f"✅ Kullanıcı: Melih Özdemir")
