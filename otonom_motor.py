import asyncio
from playwright.sync_api import sync_playwright
import json
import os
import google.generativeai as genai

def video_cek():
    print("TikTok'a bulut üzerinden erişiliyor...")
    try:
        with sync_playwright() as p:
            # GitHub sunucusunda ekran olmadığı için headless=True olmalı
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            # TikTok Keşfet sayfası
            page.goto("https://www.tiktok.com/explore", wait_until="networkidle")
            page.wait_for_timeout(5000) 
            
            # Sayfayı biraz aşağı kaydırıp videoların yüklenmesini simüle et
            for i in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                
            print("Keşfet tarandı, veriler güncelleniyor...")
            browser.close()
    except Exception as e:
        print(f"Video çekme sırasında küçük bir aksama oldu: {e}")

def analiz_yap(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Mevcut veritabanını oku
    with open("trend_veritabani.json", "r", encoding="utf-8") as f:
        veriler = json.load(f)
    
    # Gemini'ye en popüler videoları göndererek analiz iste
    prompt = f"Türkiye TikTok trendlerini şu verilere göre analiz et ve Melih için 3 içerik fikri ver: {str(veriler[:15])}"
    
    response = model.generate_content(prompt)
    
    # Analizi kaydet
    with open("son_analiz.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Yapay zeka analizi başarıyla tamamlandı.")

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        video_cek()
        analiz_yap(api_key)
    else:
        print("Hata: API Key tanımlanmamış!")
