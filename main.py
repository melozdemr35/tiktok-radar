import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import json
import os
import re
import random
from collections import Counter

# --- AYARLAR ---
DB_FILE = "trend_veritabani.json"
HESAPLAR = ["oturum_1", "oturum_2", "oturum_3", "oturum_4", "oturum_5"]

def format_sayi(num):
    try:
        n = float(num)
        if n >= 1_000_000: return f"{n / 1_000_000:.1f}M"
        if n >= 1_000: return f"{n / 1_000:.1f}K"
        return str(int(n))
    except: return "0"

class TrendCanavari:
    def __init__(self):
        self.veriler = self.db_yukle()

    def db_yukle(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                try: return json.load(f)
                except: return []
        return []

    def db_kaydet(self, yeni_gelenler):
        mevcut_id_ler = {v['id'] for v in self.veriler}
        eklenen = 0
        for v in yeni_gelenler:
            if v['id'] not in mevcut_id_ler:
                self.veriler.append(v)
                eklenen += 1
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.veriler, f, ensure_ascii=False, indent=4)
        return eklenen

    async def derin_tara(self, p, oturum_adi, link):
        scraped_data = []
        try:
            context = await p.chromium.launch_persistent_context(
                f"./{oturum_adi}", 
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.pages[0] if context.pages else await context.new_page()
            page.set_default_timeout(60000)

            async def handle_response(response):
                if "item_list" in response.url:
                    try:
                        json_data = await response.json()
                        for item in json_data.get("itemList", []):
                            desc_text = item.get("desc", "")
                            
                            resmi_hashtagler = [t.get("hashtagName") for t in item.get("textExtra", []) if t.get("hashtagName")]
                            gizli_hashtagler = re.findall(r'#(\w+)', desc_text)
                            tum_hashtagler = list(set(resmi_hashtagler + gizli_hashtagler))

                            create_time_unix = item.get("createTime")
                            gercek_tarih = datetime.fromtimestamp(int(create_time_unix)).isoformat() if create_time_unix else datetime.now().isoformat()

                            scraped_data.append({
                                "id": item.get("id"),
                                "url": f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId')}/video/{item.get('id')}",
                                "izlenme": int(item.get("stats", {}).get("playCount", 0)),
                                "begeni": int(item.get("stats", {}).get("diggCount", 0)),
                                "yorum": int(item.get("stats", {}).get("commentCount", 0)), # <--- YENİ EKLENEN YORUM ÇEKME KODU
                                "tarih": gercek_tarih,  
                                "desc": desc_text,
                                "hashtagler": tum_hashtagler,
                                "muzik": item.get("music", {}).get("title", "Bilinmeyen Ses")
                            })
                    except: pass

            page.on("response", handle_response)
            print(f"📡 {oturum_adi} doğrudan Türkiye Keşfet'e bağlanıyor...")
            await page.goto(link, wait_until="domcontentloaded")
            
            await asyncio.sleep(4)
            
            # ÇÖZÜM BURADA: Ekranda videoların olmadığı sol üst köşeye (x:10, y:10) tıklıyoruz
            await page.mouse.move(10, 10)
            await page.mouse.click(10, 10)
            
            # Fareyi sayfanın ortasına geri al (ama tıklama yapma) ki tekerlek düzgün çalışsın
            await page.mouse.move(500, 500)
            
            for i in range(40):
                kaydirma_miktari = random.randint(700, 950) 
                await page.mouse.wheel(0, kaydirma_miktari)
                
                bekleme_suresi = random.uniform(1.2, 2.2)
                await asyncio.sleep(bekleme_suresi)
                
                if i % 10 == 0: print(f"   📥 {oturum_adi} Keşfet'te kaydırıyor... Yakalanan: {len(scraped_data)}")
            
            await context.close()
        except Exception as e:
            print(f"⚠️ {oturum_adi} tarafında aksaklık oldu, atlanıyor: {e}")
        return scraped_data

    def strateji_analizi(self):
        if not self.veriler: 
            print("❌ Henüz analiz edilecek veri yok.")
            return
        
        print("\n" + "🌟" + "═"*80 + "🌟")
        print(f"   TÜRKİYE KEŞFET ANALİZ MERKEZİ | Toplam Havuz: {len(self.veriler)} Video")
        print("🌟" + "═"*80 + "🌟")

        saatler = {i: {"izl": 0, "beg": 0, "adet": 0} for i in range(24)}
        for v in self.veriler:
            try:
                h = datetime.fromisoformat(v['tarih']).hour
                saatler[h]["izl"] += v.get('izlenme', 0)
                saatler[h]["beg"] += v.get('begeni', 0)
                saatler[h]["adet"] += 1
            except: pass
        
        print("\n⏰ [STRATEJİK YÜKLEME SAATLERİ (Gerçek Veri)]")
        skorlar = sorted([(h, (s["beg"]/s["izl"]*100 if s["izl"]>0 else 0)) for h, s in saatler.items() if s["adet"]>0], key=lambda x: x[1], reverse=True)[:3]
        for h, guc in skorlar:
            print(f"⭐ {h:02d}:00 Civarı Yüklenenler | Etkileşim Gücü: %{guc:.2f}")

        print("\n🎵 [ŞU AN TÜRKİYE'DE TUTAN SESLER]")
        yasakli_sesler = ["original sound", "orijinal ses", "sonido original", "som original", "الصوت الأصلي", "son original", "оригинальный звук", "оригінальний аудіозапис", "originalton"]
        muzik_list = []
        for v in self.veriler:
            muz = v.get('muzik')
            if muz and all(yasakli not in muz.lower() for yasakli in yasakli_sesler):
                muzik_list.append(muz)

        for m, c in Counter(muzik_list).most_common(5):
            print(f"🎶 {m} ({c} Trend Videoda)")

        print("\n🏷️ [EN ÇOK ETKİLEŞİM ALAN HASHTAGLER]")
        all_tags = [t.lower() for v in self.veriler for t in v.get('hashtagler', [])]
        for tag, c in Counter(all_tags).most_common(5):
            print(f"👉 #{tag} ({c} videoda kullanıldı)")

        print("\n💎 [İLHAM ALINACAK 5 BENZERSİZ TREND]")
        gorulen_idler = set()
        benzersiz_organik = []
        
        sirali = sorted(self.veriler, key=lambda x: (x.get('begeni', 0)/x.get('izlenme', 1) if x.get('izlenme', 0)>10000 else 0), reverse=True)
        
        for v in sirali:
            if v['id'] not in gorulen_idler:
                benzersiz_organik.append(v)
                gorulen_idler.add(v['id'])
            if len(benzersiz_organik) == 5: break

        for i, v in enumerate(benzersiz_organik, 1):
            oran = (v.get('begeni', 0)/v.get('izlenme', 1)*100)
            try:
                yayin_tarihi = datetime.fromisoformat(v['tarih']).strftime("%d.%m.%Y %H:%M")
            except:
                yayin_tarihi = "Bilinmiyor"
                
            print(f"{i}. {v['url']}")
            # YENİ EKLENDİ: Terminalde de Yorum Sayısını gösteriyor
            print(f"   📅 Yüklendiği An: {yayin_tarihi} | ✨ %{oran:.1f} Beğeni Oranı | {format_sayi(v.get('izlenme', 0))} İzlenme | 💬 {format_sayi(v.get('yorum', 0))} Yorum")
            print(f"   📝 {v.get('desc', '')[:65]}...")
            print("-" * 55)

async def main():
    canavar = TrendCanavari()
    async with async_playwright() as p:
        tum_veriler = []
        for hesap in HESAPLAR:
            # Sadece Keşfet'te geziyoruz
            link = "https://www.tiktok.com/explore"
            veriler = await canavar.derin_tara(p, hesap, link)
            tum_veriler.extend(veriler)
            
        eklenen = canavar.db_kaydet(tum_veriler)
        print(f"\n✅ Havuza {eklenen} yeni benzersiz video eklendi.")
    
    canavar.strateji_analizi()

if __name__ == "__main__":
    asyncio.run(main())