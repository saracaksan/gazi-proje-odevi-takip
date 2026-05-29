import streamlit as st
import pandas as pd
import io
import os
import json
import requests
import time

# ==========================================
# 1. SAYFA YAPILANDIRMASI
# ==========================================
st.set_page_config(
    page_title="Gazi Ortaokulu | Proje Değerlendirme Sistemi",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. GÜVENLİ API AYARLARI
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    GEMINI_API_KEY = "YOK" # Kasa bulunamazsa uygulamanın tamamen çökmesini önler

    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"


# ==========================================
# 3. YÜKSEK KONTRASTLI MODERN CSS TASARIMI
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Inter:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f1f5f9; color: #0f172a; }

.hero-header { background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%); border-radius: 16px; padding: 30px; text-align: center; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2); margin-bottom: 25px; border: 1px solid #bfdbfe; }
.hero-title { font-family: 'Nunito', sans-serif; font-size: 2.4rem; font-weight: 900; color: #ffffff; margin: 0; text-shadow: 1px 2px 4px rgba(0,0,0,0.1); }
.hero-subtitle { font-size: 1.1rem; color: #e0f2fe; margin-top: 8px; font-weight: 600; }

[data-testid="stTabs"] [data-baseweb="tab-list"] { background: #e2e8f0; border-radius: 10px; padding: 5px; gap: 5px; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: #ffffff; border-radius: 6px; color: #334155; font-weight: 700; padding: 10px 20px; border: 1px solid #cbd5e1; }
[data-testid="stTabs"] [aria-selected="true"] { background: linear-gradient(135deg, #f59e0b, #d97706) !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3); }

.glass-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { 
    background-color: #f8fafc !important; border: 2px solid #94a3b8 !important; border-radius: 8px !important; color: #0f172a !important; font-weight: 600; font-size: 1rem !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #2563eb !important; background-color: #ffffff !important; }
div[data-baseweb="select"] > div { background-color: #f8fafc !important; border: 2px solid #94a3b8 !important; color: #0f172a !important; font-weight: 600; border-radius: 8px !important; }

.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label { color: #1e293b !important; font-weight: 800 !important; font-size: 0.95rem !important; }

.stButton > button { background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 800 !important; padding: 10px 20px !important; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important; }
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3) !important; }
.stDownloadButton > button { background: linear-gradient(135deg, #10b981, #059669) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER VE ÇEKİRDEK ŞABLON
# ==========================================
CONFIG_FILE = "sistem_ayarlari.json"
DATA_FILE = "veritabani.csv"

CEKIRDEK_SABLON = [
  { "id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi." },
  { "id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli hazırlanmış olması." },
  { "id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler." },
  { "id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyaller." },
  { "id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte teslim edilmesi." }
]

GEREKLI_SUTUNLAR = [
    'Okul', 'Ekleyen', 'Ders', 'S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 
    '1. Dönem Puanı', 'Proje', 'Durum', 'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON'
]
for _k in CEKIRDEK_SABLON:
    GEREKLI_SUTUNLAR.extend([f"{_k['baslik']} Puanı", f"{_k['baslik']} Açıklaması"])

# ==========================================
# 5. DOSYA VE VERİ YÖNETİMİ
# ==========================================
def ayar_yukle():
    if not os.path.exists(CONFIG_FILE):
        varsayilan = {
            "okullar": ["Gazi Ortaokulu"],
            "sablonlar": {"Gazi Matematik Şablonu": CEKIRDEK_SABLON},
            "kullanicilar": {
                "admin": {"sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi", "brans": "Tüm Dersler"}
            }
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(varsayilan, f, ensure_ascii=False, indent=4)
        return varsayilan
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "sablonlar" not in data: data["sablonlar"] = {"Gazi Matematik Şablonu": CEKIRDEK_SABLON}
        return data

def ayar_kaydet(ayarlar):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(ayarlar, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=0)
def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype={"Okul No": str})
            df.dropna(subset=['Okul No'], inplace=True)
            df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
            
            for col in ['Okul', 'Ekleyen', 'Ders', 'Dinamik_JSON']:
                if col not in df.columns:
                    df[col] = "Gazi Ortaokulu" if col == 'Okul' else ("admin" if col == 'Ekleyen' else ("Matematik" if col == 'Ders' else "{}"))
                    
            for s in GEREKLI_SUTUNLAR:
                if s not in df.columns: df[s] = None
            
            for c in df.columns:
                if "Açıklaması" in c or "Yorumu" in c or "JSON" in c or c in ["Ders", "Öğrenci Adı Soyadı"]:
                    df[c] = df[c].astype('object')
            return df
        except Exception: return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
    return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

def veriyi_kaydet(df):
    df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()

def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Ders', '1. Dönem Puanı', 'Proje', 'Durum'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Sablonu')
        worksheet = writer.sheets['Ogrenci_Sablonu']
        for col_num, _ in enumerate(sablon_df.columns.values):
            worksheet.set_column(col_num, col_num, 20)
    return output.getvalue()

# ==========================================
# 6. PROFESYONEL EXCEL ÇIKTI MOTORU
# ==========================================
def profesyonel_excel_uret(gosterilecek_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        gosterilecek_df.to_excel(writer, index=False, sheet_name='Proje_Raporu')
        workbook  = writer.book
        worksheet = writer.sheets['Proje_Raporu']
        
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#2563eb', 'font_color': 'white',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        cell_format = workbook.add_format({
            'text_wrap': True, 'align': 'left', 'valign': 'top', 'border': 1
        })
        
        for col_num, column_title in enumerate(gosterilecek_df.columns):
            worksheet.write(0, col_num, column_title, header_format)
            
        for col_num, col_name in enumerate(gosterilecek_df.columns):
            col_name_str = str(col_name)
            if "Açıklaması" in col_name_str or "Yorumu" in col_name_str or "JSON" in col_name_str:
                worksheet.set_column(col_num, col_num, 55, cell_format)
            elif "Öğrenci Adı" in col_name_str or "Proje" in col_name_str or "Ders" in col_name_str:
                worksheet.set_column(col_num, col_num, 20, cell_format)
            else:
                try:
                    gecerli_veriler = gosterilecek_df[col_name].dropna().astype(str).tolist()
                    max_len = max([len(v) for v in gecerli_veriler] + [len(col_name_str)]) if gecerli_veriler else len(col_name_str)
                except:
                    max_len = len(col_name_str)
                worksheet.set_column(col_num, col_num, max(max_len + 2, 12), cell_format)
                
        worksheet.set_row(0, 30)
    return output.getvalue()

# ==========================================
# 7. ZIRHLI YAPAY ZEKA BAĞLANTISI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    if GEMINI_API_KEY == "YOK":
        raise Exception("API Anahtarı eksik! Lütfen Streamlit Secrets paneline (API_KEY) ekleyin.")

    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye = "".join(filter(str.isdigit, sinif_str))
    seviye = seviye if seviye else "7" 
    
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])
    
    prompt = f"""Sen çok tecrübeli bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}.
Karşında {seviye}. Sınıfa giden, yaklaşık {int(seviye)+5} yaşında bir öğrenci var. Öğrenciyle doğrudan 'sen' diliyle konuşacaksın. Dilin çok akademik olmamalı, çocuğun yaşına uygun, şefkatli, eksikleri kırmadan anlatan ve onu gelişime teşvik eden bir tonda olmalı.
Değerlendirme Kriterleri ve Maksimum Puanları şunlardır:
{kriter_ozeti}

GÖREV MODU: """

    if mod == "A":
        prompt += f"""YORUMDAN PUAN ÜRETME MODU.
Öğretmenin serbest notu: "{ham_metin}"
Görev: Öğretmenin bu notunu analiz et. Öğrencinin yaşına uygun bir dille her kritere ait alt açıklamaları yaz. Öğretmenin notundaki vurgulara göre her kriter için MANTIKLI BİR PUAN (max puana göre) belirle."""
    elif mod == "B":
        prompt += f"""HEDEF PUANDAN YORUM ÜRETME MODU.
Öğretmenin belirlediği Hedef Toplam Puan: {hedef_puan} / 100
Görev: Bu hedef toplam puana ulaşacak şekilde her kritere mantıklı puanlar dağıt. Verdiğin bu puanlara uygun olarak öğrenciye motive edici açıklamalar yaz."""
    else: 
        mevcut_puan_ozeti = "\n".join([f"  - {k['id']} Kriteri: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA MODU.
Öğretmen puanları kendi girdi:
{mevcut_puan_ozeti}
Öğretmenin ekstra notu (varsa): "{ham_metin}"
Görev: Sadece verilen bu puanlara bakarak, öğrenci seviyesine uygun motive edici açıklamalar yaz. Puanları KESİNLİKLE DEĞİŞTİRME, sana ne verildiyse aynısını JSON formatına geçir."""

    prompt += f"""

EKSTRA İSTENEN:
"genel": Öğrenciye bu dersin hayatındaki öneminden kısaca bahseden, eksiklerini düzeltmezse neler olabileceğini tatlıca anlatan ve başarılar dileyen genel bir yorum.

DİKKAT: SADECE GEÇERLİ JSON FORMATINDA CEVAP VER. BAŞKA HİÇBİR METİN VEYA İŞARET KULLANMA. JSON FORMATI ŞU ŞEKİLDE OLMALI:
{{
  "puanlar": {{ "{kriterler[0]['id']}": 40 }},
  "aciklamalar": {{ "{kriterler[0]['id']}": "Açıklama..." }},
  "genel": "Genel yorum..."
}}"""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    
    try:
        response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
        response.raise_for_status()
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Zırhlı JSON temizleme (Kopma veya syntax hatasını kesin engeller)
        raw_text = raw_text.replace('```json', '')
        raw_text = raw_text.replace('```', '')
        raw_text = raw_text.strip()
        
        return json.loads(raw_text)
    except Exception as e:
        raise Exception(f"Google AI Hatası: {e}")
# ==========================================
# 7.5. YAPAY ZEKA KARNE GÖRÜŞÜ MOTORU
# ==========================================
def ai_karne_gorusu_yaz(ogrenci_adi, sinifi, notlar_sozlugu, davranis_notu, ogrt_ad):
    if GEMINI_API_KEY == "YOK":
        raise Exception("API Anahtarı eksik! Lütfen Streamlit Secrets paneline ekleyin.")

    # Sınıftan yaş/seviye tahmini (Örn: "6/C" -> 6. Sınıf -> ~11 yaş)
    seviye_str = "".join(filter(str.isdigit, str(sinifi)))
    seviye = int(seviye_str) if seviye_str else 4
    
    # Notları okunabilir bir metne çeviriyoruz (Sadece notu girilmiş olanlar)
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu) and str(notu).strip() != ""])

    prompt = f"""Sen bir sınıf rehber öğretmenisin. Adın {ogrt_ad}.
Karşında {sinifi} sınıfından (yaklaşık {seviye+5} yaşında) {ogrenci_adi} adında bir öğrencin var. 
Dönem sonu karnesini veriyorsun. Öğrenciyle doğrudan 'sen' diliyle konuşarak şefkatli, pedagojik, bilimsel ve yaşına tam uygun bir karne görüşü yazacaksın.

Öğrencinin Ders Notları (100 Üzerinden):
{notlar_metni}

Öğretmenin Davranış ve Gelişim Gözlemi: "{davranis_notu if davranis_notu else 'Genel iyi hal ve akademik çaba.'}"

Görev ve Kurallar:
1. Öğrencinin yüksek olan notlarını överek akademik başarısını takdir et ve motive et.
2. Düşük olan notları (varsa) için onu asla kırmadan, "planlı çalışırsak ve bu konularda pratik yaparsak toparlarız, potansiyeline inanıyorum" tarzında yol gösterici bir dil kullan.
3. Öğretmenin davranış gözlemini (eğer girilmişse) metnin içine çok doğal ve sosyal gelişimini destekleyecek şekilde yedir.
4. Toplam 3-4 cümlelik, resmiyetten uzak ama saygın bir öğretmen tonunda, öğrencinin ismine hitap eden, e-Okul'a veya doğrudan karneye yapıştırılabilecek bir metin olsun.

SADECE KARNE GÖRÜŞÜ METNİNİ YAZ. Başka hiçbir açıklama, tırnak işareti, giriş cümlesi veya JSON formatı KULLANMA."""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    
    try:
        response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        raise Exception(f"Google AI Karne Görüşü Hatası: {e}")
# ==========================================
# 8. CANLI VE DİNAMİK HTML KARNE OLUŞTURUCU
# ==========================================
def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Proje Karneleri</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 20px; }}
  .page {{ background: white; width: 210mm; margin: 0 auto 20px; padding: 15mm; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); page-break-after: always; border-top: 8px solid #3b82f6; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
  th {{ background: #f8fafc; color: #1e293b; padding: 12px; text-align: left; font-size: 0.9rem; border-bottom: 2px solid #cbd5e1; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem; vertical-align: top; line-height: 1.6; color: #334155; }}
  .header {{ background: linear-gradient(135deg, #2563eb, #38bdf8); color: white; padding: 25px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 10px rgba(37,99,235,0.2); }}
  .student-info {{ display: flex; gap: 20px; margin-top: 20px; padding: 15px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #38bdf8; }}
  .info-item {{ display: flex; flex-direction: column; }}
  .info-label {{ font-size: 0.75rem; color: #64748b; font-weight: bold; text-transform: uppercase; }}
  .info-value {{ font-size: 1.05rem; font-weight: 800; color: #0f172a; }}
  .yorum-kutu {{ background: #fffbeb; padding: 20px; margin-top: 25px; border-radius: 8px; border-left: 5px solid #f59e0b; line-height: 1.7; color: #78350f; font-size: 0.95rem; }}
  .imza {{ text-align: right; margin-top: 40px; color: #475569; font-size: 1rem; }}
  @media print {{ body {{ background: white; padding: 0; }} .page {{ box-shadow: none; margin: 0; border-top: none; }} .header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style></head><body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        top_raw = b.get('Toplam Puan', 0)
        toplam = int(pd.to_numeric(top_raw, errors='coerce')) if pd.notna(top_raw) else 0
        renk = "#10b981" if toplam >= 85 else ("#f59e0b" if toplam >= 60 else "#ef4444")
        
        dinamik_puanlar = {}
        try:
            din_json = str(b.get('Dinamik_JSON', '{}'))
            if din_json.strip() and din_json != "nan":
                dinamik_puanlar = json.loads(din_json)
        except: pass

        html += f"""
<div class="page">
  <div class="header">
    <div>
        <div style="font-size:0.9rem; opacity:0.9; letter-spacing:1px; text-transform:uppercase; font-weight:bold;">{b.get('Okul', 'Okul')}</div>
        <h1 style="margin: 5px 0 0; font-size:1.8rem;">{b.get('Ders', ogrt_brans)} Proje Raporu</h1>
    </div>
    <div style="text-align: center;">
        <div style="font-size: 2.8rem; font-weight: 900; background: white; color: {renk}; padding: 5px 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{toplam}</div>
        <div style="font-size: 0.8rem; margin-top: 8px; opacity: 0.9; font-weight: bold;">TOPLAM PUAN</div>
    </div>
  </div>
  
  <div class="student-info">
    <div class="info-item"><span class="info-label">Öğrenci Adı Soyadı</span><span class="info-value">{b.get('Öğrenci Adı Soyadı','')}</span></div>
    <div class="info-item"><span class="info-label">Sınıf</span><span class="info-value">{b.get('Sınıf','')}</span></div>
    <div class="info-item"><span class="info-label">Okul No</span><span class="info-value">{b.get('Okul No','')}</span></div>
  </div>

  <table>
    <tr><th style="width:25%;">Değerlendirme Kriteri</th><th style="width:10%; text-align:center;">Max</th><th style="width:10%; text-align:center;">Puan</th><th style="width:55%;">Öğretmen Değerlendirmesi</th></tr>
"""
        for k in aktif_kriterler:
            p_raw = dinamik_puanlar.get(f"{k['id']}_puan", b.get(f"{k['baslik']} Puanı", 0))
            p = int(pd.to_numeric(p_raw, errors='coerce')) if pd.notna(p_raw) else 0
            a = dinamik_puanlar.get(f"{k['id']}_aciklama", b.get(f"{k['baslik']} Açıklaması", "-"))
            
            if pd.isna(a) or str(a).strip() == "" or str(a).strip() == "nan": a = "Değerlendirme girilmedi."
            
            p_renk = "#10b981" if (p/k['max']) >= 0.8 else ("#f59e0b" if (p/k['max']) >= 0.5 else "#ef4444")
            html += f"<tr><td><strong>{k['baslik']}</strong></td><td style='text-align:center; color:#64748b; font-weight:bold;'>{k['max']}</td><td style='text-align:center; font-weight:900; font-size:1.1rem; color:{p_renk};'>{p}</td><td>{a}</td></tr>"
        
        genel = str(b.get('Genel Değerlendirme Yorumu', '-'))
        if pd.isna(genel) or not genel.strip() or genel.strip() == "nan": genel = "Genel değerlendirme yapılmadı."
        
        html += f"""
  </table>
  <div class="yorum-kutu"><strong>💬 Genel Değerlendirme & Gelecek Tavsiyeleri:</strong><br><br>{genel}</div>
  <div class="imza"><strong>{ogrt_ad}</strong><br>{b.get('Ders', ogrt_brans)} Öğretmeni</div>
</div>
"""
    html += "</body></html>"
    return html

# ==========================================
# 9. ÖĞRENCİ PANELİ
# ==========================================
def ogrenci_paneli(df, ayarlar):
    st.markdown("<h2 style='text-align:center; color:#1e293b; font-weight:900; margin-bottom: 30px;'>🎓 Akıllı Karne Sorgulama Paneli</h2>", unsafe_allow_html=True)
    if df.empty:
        st.warning("⚠️ Sisteme henüz veri yüklenmemiştir.")
        return

    col_m = st.columns([1, 2, 1])[1]
    with col_m:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        okullar = ["— Okul Seçiniz —"] + ayarlar["okullar"]
        secili_okul = st.selectbox("🏫 Okulunuz", okullar)
        siniflar = ["— Sınıf Seçiniz —"] + sorted(df[df['Okul'] == secili_okul]['Sınıf'].dropna().unique().tolist()) if secili_okul != "— Okul Seçiniz —" else ["Önce okul seçin"]
        secili_sinif = st.selectbox("📚 Sınıfınız", siniflar)
        okul_no = st.text_input("🔢 Okul Numaranız")
        sorgula = st.button("🔍 Karnemi Bul ve Göster", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if sorgula:
        if secili_okul == "— Okul Seçiniz —" or secili_sinif in ["— Sınıf Seçiniz —", "Önce okul seçin"] or not okul_no.strip():
            st.error("❌ Lütfen okulunuzu, sınıfınızı seçin ve numaranızı eksiksiz girin.")
        else:
            ogrenci_projeleri = df[(df['Okul'] == secili_okul) & (df['Sınıf'] == secili_sinif) & (df['Okul No'] == okul_no.strip())]
            if ogrenci_projeleri.empty:
                st.error("❌ Sistemde bu bilgilere ait kayıt bulunamadı.")
            else:
                bilgi = ogrenci_projeleri.iloc[0] 
                
                ogrt_ad, ogrt_brans = "Proje Öğretmeni", bilgi.get('Ders', "Genel")
                if bilgi.get('Ekleyen') != 'admin':
                     user_data = ayarlar["kullanicilar"].get(bilgi.get('Ekleyen'), {})
                     ogrt_ad = user_data.get("ad", "Öğretmen")
                     ogrt_brans = user_data.get("brans", ogrt_brans)

                st.success(f"🎉 Harika! Hoş geldin, {bilgi.get('Öğrenci Adı Soyadı', '')}!")
                st.info("💡 Karneni renkli formatta cihazına indirmek veya yazdırmak için aşağıdaki butonu kullanabilirsin.")
                
                kullanilan_sablon = CEKIRDEK_SABLON 
                tek_df = pd.DataFrame([bilgi])
                html_karne = toplu_karne_html_dosyasi_uret(tek_df, ogrt_ad, ogrt_brans, kullanilan_sablon)
                
                st.components.v1.html(html_karne, height=700, scrolling=True)
                
                col_indir = st.columns([1, 2, 1])[1]
                with col_indir:
                    st.download_button("🖨️ PDF / HTML Olarak İndir", data=html_karne, file_name=f"{bilgi['Ders']}_Karne_{bilgi['Okul No']}.html", mime="text/html", use_container_width=True)

# ==========================================
# 10. YETKİLİ GİRİŞ PANELİ
# ==========================================
def giris_paneli(ayarlar):
    col_m = st.columns([1, 1.2, 1])[1]
    with col_m:
        st.markdown('<div class="glass-card" style="padding:40px; text-align:center;">', unsafe_allow_html=True)
        st.markdown("<h2 style='color:#2563eb; font-weight:900;'>🔐 Sisteme Giriş</h2>", unsafe_allow_html=True)
        k_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("🚀 Giriş Yap", use_container_width=True):
            kullanici = ayarlar["kullanicilar"].get(k_adi)
            if kullanici and kullanici["sifre"] == sifre:
                st.session_state["giris_yapti"] = True
                st.session_state["aktif_kullanici"] = k_adi
                st.session_state["kullanici_bilgi"] = kullanici
                st.rerun()
            else: 
                st.error("❌ Hatalı kullanıcı adı veya şifre!")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 11. YÖNETİM VE ÖĞRETMEN ANA PANELİ
# ==========================================
def yonetim_paneli(df, ayarlar):
    aktif_id = st.session_state["aktif_kullanici"]
    k_bilgi = st.session_state["kullanici_bilgi"]
    rol = k_bilgi["rol"]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:linear-gradient(135deg, #dbeafe, #bfdbfe); border:2px solid #93c5fd; border-radius:12px; padding:15px; margin-bottom:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
      <div>
        <div style="font-weight:900; color:#1e40af; font-size:1.3rem;">👋 Hoş Geldiniz, {k_bilgi['ad']}</div>
        <div style="color:#2563eb; font-size:0.95rem; font-weight:700;">Yetki: {'Sistem Yöneticisi' if rol == 'admin' else f"{k_bilgi.get('okul', '')} - {k_bilgi.get('brans', '')} Öğretmeni"}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Güvenli Çıkış Yap"):
        st.session_state.clear()
        st.rerun()

    if rol == "admin": 
        df_yetkili = df
        sekmeler = st.tabs(["🏢 Şablon ve Sistem", "📂 Öğrenci Yükle/Ekle", "🤖 Akıllı Değerlendirme & AI", "📊 Dar / Geniş Raporlar", "📝 Akıllı Karne Görüşü"])
    else: 
        df_yetkili = df[(df['Okul'] == k_bilgi.get("okul")) & (df['Ekleyen'] == aktif_id)]
        sekmeler = st.tabs(["📂 Öğrenci Yükle/Ekle", "🤖 Akıllı Değerlendirme & AI", "📊 Dar / Geniş Raporlar", "📝 Akıllı Karne Görüşü"])
 # --- SEKME 1 (ADMİN): SİSTEM VE ŞABLON ---
    if rol == "admin":
        with sekmeler[0]:
            st.markdown("### 📚 Görsel ve Dinamik Şablon Oluşturucu")
            st.info("💡 Aşağıdaki tabloya tıklayarak yeni kriterler yazabilir, en alta inerek yeni satır ekleyebilir veya gereksiz satırları silebilirsiniz. Toplam 100 puan olmalıdır.")
            
            # Düzenleme modu için hafıza (Session State) kontrolü
            if "edit_sablon_adi" not in st.session_state:
                st.session_state["edit_sablon_adi"] = ""
            if "taslak_df" not in st.session_state:
                st.session_state["taslak_df"] = pd.DataFrame([
                    {"Kriter Başlığı": "İçerik", "Maksimum Puan": 50, "Açıklama": "Ödevdeki bilgilerin doğruluğu."},
                    {"Kriter Başlığı": "Düzen ve Sunum", "Maksimum Puan": 50, "Açıklama": "Ödevin temizliği ve görselliği."}
                ])

            c_isim, c_kayit = st.columns([3, 1])
            s_isim = c_isim.text_input("Şablonun Adı (Örn: 10 Maddelik Fen Şablonu)", value=st.session_state["edit_sablon_adi"])
            
            # Dinamik Excel benzeri tablo
            edited_df = st.data_editor(
                st.session_state["taslak_df"], 
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )
            
            toplam_puan = pd.to_numeric(edited_df["Maksimum Puan"], errors="coerce").fillna(0).sum()
            
            if toplam_puan == 100:
                st.success(f"✅ Kriterlerin toplamı 100 puan. Şablon kaydedilmeye hazır!")
            else:
                st.error(f"⚠️ Kriterlerin toplamı tam 100 puan olmalıdır! (Şu anki toplam: {toplam_puan})")
            
            if st.button("💾 Tablodaki Şablonu Kaydet / Güncelle", use_container_width=True):
                if not s_isim.strip():
                    st.error("❌ Lütfen şablona bir isim verin!")
                elif toplam_puan != 100:
                    st.error("❌ Toplam puan 100 olmadan kayıt yapamazsınız!")
                else:
                    yeni_kriterler = []
                    for i, row in edited_df.iterrows():
                        yeni_kriterler.append({
                            "id": f"k{i+1}",
                            "baslik": str(row["Kriter Başlığı"]),
                            "max": int(row["Maksimum Puan"]),
                            "icon": "📌",
                            "aciklama": str(row["Açıklama"])
                        })
                    
                    ayarlar["sablonlar"][s_isim] = yeni_kriterler
                    ayar_kaydet(ayarlar)
                    st.session_state["edit_sablon_adi"] = ""
                    st.session_state["taslak_df"] = pd.DataFrame([{"Kriter Başlığı": "İçerik", "Maksimum Puan": 50, "Açıklama": "..."}])
                    st.success(f"✅ '{s_isim}' başarıyla kaydedildi/güncellendi!")
                    time.sleep(1)
                    st.rerun()
            
            st.markdown("---")
            c_mevcut, c_ogrt = st.columns(2)
            
            with c_mevcut:
                st.markdown("#### ⚙️ Şablon Düzenle / Sil")
                mevcut_sablonlar = list(ayarlar.get("sablonlar", {}).keys())
                secili_islem_sablonu = st.selectbox("İşlem Yapılacak Şablonu Seçin:", ["— Seçiniz —"] + mevcut_sablonlar)
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✏️ Düzenle", use_container_width=True) and secili_islem_sablonu != "— Seçiniz —":
                        secili_data = ayarlar["sablonlar"][secili_islem_sablonu]
                        df_data = []
                        for k in secili_data:
                            df_data.append({"Kriter Başlığı": k["baslik"], "Maksimum Puan": k["max"], "Açıklama": k["aciklama"]})
                        st.session_state["taslak_df"] = pd.DataFrame(df_data)
                        st.session_state["edit_sablon_adi"] = secili_islem_sablonu
                        st.rerun() 
                        
                with c_btn2:
                    if st.button("🗑️ Sil", use_container_width=True) and secili_islem_sablonu != "— Seçiniz —":
                        if secili_islem_sablonu == "Gazi Matematik Şablonu":
                            st.error("❌ Varsayılan sistem şablonu silinemez!")
                        else:
                            del ayarlar["sablonlar"][secili_islem_sablonu]
                            ayar_kaydet(ayarlar)
                            st.success(f"✅ '{secili_islem_sablonu}' başarıyla silindi!")
                            time.sleep(1)
                            st.rerun()
            
            with c_ogrt:
                st.markdown("#### 👨‍🏫 Gelişmiş Öğretmen Yönetimi")
                
                ogretmenler = {k: v for k, v in ayarlar["kullanicilar"].items() if v.get("rol") == "ogretmen"}
                
                t_ekle, t_liste, t_duzenle = st.tabs(["➕ Ekle", "📋 Listele / Sil", "✏️ Düzenle"])
                
                with t_ekle:
                    st.info("💡 Bir öğretmene birden fazla branş atamak için aralarına virgül koyun (Örn: Matematik, Zeka Oyunları)")
                    with st.form("ogrt_ekle_form"):
                        o_okul = st.selectbox("Okulu", ayarlar["okullar"])
                        c1, c2 = st.columns(2)
                        o_kadi = c1.text_input("Kullanıcı Adı (Giriş İçin)")
                        o_sifre = c2.text_input("Şifre")
                        o_ad = c1.text_input("Ad Soyad")
                        o_brans = c2.text_input("Branş(lar)")
                        if st.form_submit_button("💾 Öğretmeni Sisteme Ekle", use_container_width=True):
                            if not o_kadi or not o_sifre or not o_ad:
                                st.error("❌ Kullanıcı adı, şifre ve ad soyad zorunludur!")
                            elif o_kadi in ayarlar["kullanicilar"]:
                                st.error("❌ Bu kullanıcı adı sistemde zaten kayıtlı!")
                            else:
                                ayarlar["kullanicilar"][o_kadi] = {"sifre": o_sifre, "rol": "ogretmen", "ad": o_ad, "okul": o_okul, "brans": o_brans}
                                ayar_kaydet(ayarlar)
                                st.success(f"✅ {o_ad} başarıyla eklendi!")
                                time.sleep(1)
                                st.rerun()

                with t_liste:
                    if not ogretmenler:
                        st.warning("⚠️ Sistemde henüz kayıtlı öğretmen bulunmuyor.")
                    else:
                        for kadi, data in ogretmenler.items():
                            with st.expander(f"👤 {data['ad']} - ({data.get('brans', 'Branş Yok')})"):
                                st.write(f"**Giriş ID:** `{kadi}`")
                                st.write(f"**Şifresi:** `{data['sifre']}`")
                                st.write(f"**Okulu:** {data.get('okul', 'Belirtilmedi')}")
                                if st.button(f"🗑️ Bu Öğretmeni Sil", key=f"sil_{kadi}", use_container_width=True):
                                    del ayarlar["kullanicilar"][kadi]
                                    ayar_kaydet(ayarlar)
                                    st.success(f"✅ {data['ad']} sistemden tamamen silindi!")
                                    time.sleep(1)
                                    st.rerun()

                with t_duzenle:
                    if not ogretmenler:
                        st.warning("⚠️ Düzenlenecek öğretmen bulunmuyor.")
                    else:
                        duzenle_kadi = st.selectbox("Düzenlenecek Öğretmeni Seçin", list(ogretmenler.keys()), format_func=lambda x: f"{ogretmenler[x]['ad']} ({x})")
                        if duzenle_kadi:
                            d_data = ogretmenler[duzenle_kadi]
                            with st.form("ogrt_duzenle_form"):
                                d_okul_idx = ayarlar["okullar"].index(d_data.get('okul')) if d_data.get('okul') in ayarlar["okullar"] else 0
                                d_okul = st.selectbox("Okulu", ayarlar["okullar"], index=d_okul_idx)
                                c1, c2 = st.columns(2)
                                d_sifre = c1.text_input("Yeni Şifre", value=d_data['sifre'])
                                d_ad = c2.text_input("Ad Soyad", value=d_data['ad'])
                                d_brans = st.text_input("Branş(lar)", value=d_data.get('brans', ''))
                                
                                if st.form_submit_button("🔄 Bilgileri Güncelle", use_container_width=True):
                                    ayarlar["kullanicilar"][duzenle_kadi].update({"sifre": d_sifre, "ad": d_ad, "okul": d_okul, "brans": d_brans})
                                    ayar_kaydet(ayarlar)
                                    st.success("✅ Öğretmen bilgileri başarıyla güncellendi!")
                                    time.sleep(1)
                                    st.rerun()

    # --- SEKME: ÖĞRENCİ YÜKLEME VE EKLEME ---
    sekme_veri = sekmeler[1] if rol == "admin" else sekmeler[0]
    with sekme_veri:
        t1, t2, t3 = st.tabs(["📥 Excel Yükle", "➕ Manuel Ekle", "🗑️ Öğrenci Sil"])
        
        with t1:
            hedef_okul = st.selectbox("Okul", ayarlar["okullar"], key="hedef_okul_excel") if rol == "admin" else k_bilgi.get("okul")
            c1, c2 = st.columns(2)
            with c1: st.download_button("📄 Boş Şablonu İndir", data=bos_sablon_olustur(), file_name="Sablon.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with c2:
                yuklenen = st.file_uploader("Doldurduğunuz Excel'i Yükleyin", type=['xlsx'])
                if yuklenen and st.button("💾 Yükle", use_container_width=True):
                    try:
                        yeni_df = pd.read_excel(yuklenen, dtype={"Okul No": str})
                        yeni_df['Okul No'] = yeni_df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
                        yeni_df.dropna(subset=['Okul No'], inplace=True)
                        mevcut_nolar = df[df['Okul'] == hedef_okul]['Okul No'].tolist()
                        eklenecek = yeni_df[~yeni_df['Okul No'].isin(mevcut_nolar)].copy()
                        if not eklenecek.empty:
                            eklenecek['Okul'] = hedef_okul
                            eklenecek['Ekleyen'] = aktif_id
                            eklenecek['Dinamik_JSON'] = "{}"
                            for s in GEREKLI_SUTUNLAR:
                                if s not in eklenecek.columns: eklenecek[s] = None
                            df = pd.concat([df, eklenecek[GEREKLI_SUTUNLAR]], ignore_index=True)
                            veriyi_kaydet(df)
                            st.success(f"✅ {len(eklenecek)} öğrenci eklendi!")
                            time.sleep(1)
                            st.rerun()
                        else: st.warning("Bu öğrenciler zaten sistemde var!")
                    except Exception as e: st.error(f"Hata: {e}")
        
        with t2:
            with st.form("m_ekle"):
                e_okul = st.selectbox("Okul Seç", ayarlar["okullar"], key="e_okul_manuel") if rol == "admin" else k_bilgi.get("okul")
                c1, c2 = st.columns(2)
                e_no = c1.text_input("Okul Numarası")
                e_ad = c2.text_input("Ad Soyad")
                e_sinif = c1.text_input("Sınıf")
                e_ders = c2.text_input("Ders (Örn: Fen Bilimleri)", value=k_bilgi.get("brans", ""))
                if st.form_submit_button("Öğrenciyi Ekle"):
                    if e_no and e_ad:
                        yeni = {col: None for col in GEREKLI_SUTUNLAR}
                        yeni.update({'Okul': e_okul, 'Ekleyen': aktif_id, 'Okul No': e_no.strip(), 'Öğrenci Adı Soyadı': e_ad.strip(), 'Sınıf': e_sinif.strip(), 'Ders': e_ders.strip(), 'Dinamik_JSON': "{}"})
                        df.loc[len(df)] = yeni
                        veriyi_kaydet(df)
                        st.success("Eklendi!")
                        st.rerun()
        with t3:
            st.markdown("#### 🗑️ Öğrenci ve Sınıf Silme İşlemleri")
            if df_yetkili.empty:
                st.warning("⚠️ Sistemde silinebilecek veri bulunmuyor.")
            else:
                # 3 Farklı Silme Seçeneği
                sil_tipi = st.radio("Yapmak İstediğiniz İşlem Türü:", ["👤 Tek Bir Öğrenciyi Sil", "📚 Sınıftaki Tüm Öğrencileri Toplu Sil", "🏢 Okuldaki Tüm Öğrencileri Toplu Sil"], horizontal=True)
                
                # 1. SEÇENEK: TEKİL SİLME
                if sil_tipi == "👤 Tek Bir Öğrenciyi Sil":
                    sil_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} ({r['Ders']})", axis=1).tolist()
                    sec_sil = st.selectbox("Silinecek Öğrenciyi Seçin:", ["— Seçiniz —"] + sil_liste)
                    if sec_sil != "— Seçiniz —" and st.button("🗑️ Öğrenciyi Tamamen SİL"):
                        s_no = sec_sil.split(" - ")[0]
                        df = df[~(df['Okul No'] == s_no)]
                        veriyi_kaydet(df)
                        st.success("✅ Öğrenci sistemden silindi!")
                        time.sleep(1)
                        st.rerun()
                        
                # 2. SEÇENEK: SINIF BAZLI TOPLU SİLME
                elif sil_tipi == "📚 Sınıftaki Tüm Öğrencileri Toplu Sil":
                    s_okul = st.selectbox("İşlem Yapılacak Okul:", df_yetkili['Okul'].unique())
                    s_siniflar = df_yetkili[df_yetkili['Okul'] == s_okul]['Sınıf'].dropna().unique().tolist()
                    
                    if s_siniflar:
                        s_sinif = st.selectbox("Tamamen Silinecek Sınıf:", ["— Seçiniz —"] + s_siniflar)
                        if s_sinif != "— Seçiniz —":
                            st.warning(f"⚠️ DİKKAT: **{s_okul}** okulundaki **{s_sinif}** sınıfına ait tüm öğrenciler silinecek!")
                            if st.button(f"🗑️ Evet, {s_sinif} Sınıfını Komple SİL"):
                                sart = (df['Okul'] == s_okul) & (df['Sınıf'] == s_sinif)
                                # Eğer öğretmen ise sadece kendi eklediği öğrencileri silebilir (Admin ise hepsini siler)
                                if rol != "admin": 
                                    sart = sart & (df['Ekleyen'] == aktif_id)
                                df = df[~sart]
                                veriyi_kaydet(df)
                                st.success(f"✅ {s_sinif} sınıfındaki öğrenciler temizlendi!")
                                time.sleep(1.5)
                                st.rerun()
                    else:
                        st.info("Bu okulda kayıtlı sınıf bulunmuyor.")
                        
                # 3. SEÇENEK: OKUL BAZLI TOPLU SİLME
                elif sil_tipi == "🏢 Okuldaki Tüm Öğrencileri Toplu Sil":
                    s_okul = st.selectbox("Tamamen Silinecek Okul:", df_yetkili['Okul'].unique())
                    st.error(f"🚨 ÇOK ÖNEMLİ UYARI: **{s_okul}** okuluna ait TÜM ÖĞRENCİLER ve NOTLAR kalıcı olarak silinecektir!")
                    
                    # Güvenlik için yazılı onay
                    teyit = st.text_input("Bu işlemi onaylamak için kutuya büyük harflerle 'SİL' yazın:")
                    if st.button("🗑️ Okulun Tüm Verilerini SİL"):
                        if teyit == "SİL":
                            sart = (df['Okul'] == s_okul)
                            if rol != "admin": 
                                sart = sart & (df['Ekleyen'] == aktif_id)
                            df = df[~sart]
                            veriyi_kaydet(df)
                            st.success(f"✅ {s_okul} okuluna ait tüm veriler sıfırlandı!")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("❌ İşlemi gerçekleştirebilmek için kutuya tam olarak 'SİL' yazmalısınız.")
    # --- SEKME: 3 MODLU AI DEĞERLENDİRME ---
    sekme_puan = sekmeler[2] if rol == "admin" else sekmeler[1]
    with sekme_puan:
        if df_yetkili.empty: 
            st.warning("⚠️ Değerlendirilecek öğrenci bulunmuyor.")
        else:
            c_sec, c_sablon = st.columns([2, 1])
            puan_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} ({r['Ders']})", axis=1).tolist()
            sec_p = c_sec.selectbox("🎓 Öğrenci Seçin", ["— Seçiniz —"] + puan_liste)
            
            sablon_isimleri = list(ayarlar.get("sablonlar", {}).keys())
            secili_sablon_ismi = c_sablon.selectbox("📐 Kullanılacak Şablon", sablon_isimleri)
            aktif_sablon = ayarlar["sablonlar"].get(secili_sablon_ismi, CEKIRDEK_SABLON)
            
            if sec_p != "— Seçiniz —":
                p_no = sec_p.split(" - ")[0]
                idx = df[df['Okul No'] == p_no].index[0]
                bilgi = df.iloc[idx]
                d_ad = k_bilgi.get("ad", "Yönetici")
                d_brans = bilgi.get("Ders", "Genel")
                
                if st.session_state.get("aktif_ogr_idx") != idx:
                    st.session_state["aktif_ogr_idx"] = idx
                    eski_puanlar = {}
                    try:
                        din_json = str(bilgi.get('Dinamik_JSON', '{}'))
                        if din_json.strip() and din_json != "nan":
                            eski_puanlar = json.loads(din_json)
                    except: pass
                    
                    for k in aktif_sablon:
                        eski_p = eski_puanlar.get(f"{k['id']}_puan", bilgi.get(f"{k['baslik']} Puanı", 0))
                        eski_a = eski_puanlar.get(f"{k['id']}_aciklama", bilgi.get(f"{k['baslik']} Açıklaması", ""))
                        st.session_state[f"w_puan_{k['id']}"] = int(pd.to_numeric(eski_p, errors='coerce')) if pd.notna(eski_p) else 0
                        st.session_state[f"w_aciklama_{k['id']}"] = str(eski_a) if pd.notna(eski_a) and str(eski_a) != "nan" else ""
                    
                    eski_g = bilgi.get('Genel Değerlendirme Yorumu', "")
                    st.session_state["w_genel"] = str(eski_g) if pd.notna(eski_g) and str(eski_g) != "nan" else ""

                st.markdown('<div class="glass-card" style="background:#eff6ff; border-color:#93c5fd;">', unsafe_allow_html=True)
                ai_modu = st.radio("🤖 YAPAY ZEKA ÇALIŞMA MODU:", 
                                   options=["A", "B", "C"], 
                                   format_func=lambda x: {
                                       "A": "MOD A: Yorum Yaz, Puanı ve Açıklamaları AI Dağıtsın",
                                       "B": "MOD B: Sadece Hedef Puanı Gir, AI Tüm Dağılımı ve Yorumu Yapsın",
                                       "C": "MOD C: Manuel Puanla, AI Sadece Yorum Yapsın"
                                   }[x], horizontal=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                ham_metin, hedef_puan = "", 100
                if ai_modu == "A": ham_metin = st.text_area("Öğretmen Notunuz (AI buna göre puan dağıtacak):")
                elif ai_modu == "B": hedef_puan = st.number_input("Karnede Görünmesini İstediğiniz Hedef Puan (0-100)", 0, 100, 85)
                elif ai_modu == "C": ham_metin = st.text_input("AI'a özel ekstra notunuz (Opsiyonel):")

                if st.button("✨ Yapay Zekayı Çalıştır (Kutuları Otomatik Doldurur)", use_container_width=True):
                    with st.spinner("🤖 AI Düşünüyor..."):
                        try:
                            manuel_puan_dict = {k['id']: st.session_state.get(f"w_puan_{k['id']}", 0) for k in aktif_sablon}
                            json_sonuc = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, manuel_puan_dict, d_ad, d_brans)
                            
                            for k in aktif_sablon:
                                if k['id'] in json_sonuc.get("puanlar", {}):
                                    st.session_state[f"w_puan_{k['id']}"] = int(json_sonuc["puanlar"][k['id']])
                                if k['id'] in json_sonuc.get("aciklamalar", {}):
                                    st.session_state[f"w_aciklama_{k['id']}"] = json_sonuc["aciklamalar"][k['id']]
                            if "genel" in json_sonuc:
                                st.session_state["w_genel"] = json_sonuc["genel"]
                            
                            st.success("✅ AI İşlemi Tamamlandı! Lütfen aşağıdaki kutuları kontrol edip KAYDET butonuna basın.")
                            time.sleep(1)
                            st.rerun() 
                        except Exception as e:
                            st.error(f"❌ AI Hatası: {e}")

                st.markdown("---")
                st.markdown("### 📝 Gözden Geçirme ve Kayıt Alanı")
                
                for k in aktif_sablon:
                    c1, c2 = st.columns([1, 4])
                    c1.number_input(f"{k['baslik']} (Max:{k['max']})", 0, k['max'], key=f"w_puan_{k['id']}")
                    c2.text_area(f"Açıklama ({k['baslik']})", key=f"w_aciklama_{k['id']}")
                
                st.text_area("💬 Genel Değerlendirme Yorumu", key="w_genel", height=120)
                
                if st.button("💾 Yukarıdaki Puanları ve Yorumları Veritabanına Kaydet", use_container_width=True):
                    dinamik_kayit = {}
                    toplam = 0
                    for k in aktif_sablon:
                        p_val = st.session_state[f"w_puan_{k['id']}"]
                        a_val = st.session_state[f"w_aciklama_{k['id']}"]
                        dinamik_kayit[f"{k['id']}_puan"] = p_val
                        dinamik_kayit[f"{k['id']}_aciklama"] = a_val
                        df.at[idx, f"{k['baslik']} Puanı"] = p_val
                        df.at[idx, f"{k['baslik']} Açıklaması"] = str(a_val)
                        toplam += p_val
                    
                    df.at[idx, 'Dinamik_JSON'] = json.dumps(dinamik_kayit, ensure_ascii=False)
                    df.at[idx, 'Genel Değerlendirme Yorumu'] = str(st.session_state["w_genel"])
                    df.at[idx, 'Toplam Puan'] = toplam
                    veriyi_kaydet(df)
                    st.success(f"✅ Mükemmel! Kaydedildi. Toplam Puan: {toplam}")

    # --- SEKME: DAR / GENİŞ RAPORLAR ---
    sekme_rapor = sekmeler[3] if rol == "admin" else sekmeler[2]
# --- SEKME: PROFESYONEL RAPORLAR ---
    sekme_rapor = sekmeler[3] if rol == "admin" else sekmeler[2]
    with sekme_rapor:
        if df_yetkili.empty: 
            st.warning("⚠️ Raporlanacak veri bulunmuyor.")
        else:
            st.markdown("### 📊 Gelişmiş Raporlama ve Çıktı Merkezi")
            
            # Sınıf Seçimi ve Şablon Tespiti
            r_sinif = st.selectbox("Raporlanacak Sınıfı Seçin", sorted(df_yetkili['Sınıf'].dropna().unique()))
            df_yazdir = df_yetkili[df_yetkili['Sınıf'] == r_sinif]
            
            # Sınıftaki ilk öğrencinin şablonunu referans alıyoruz (İdare matrisi için gerekli)
            aktif_kriterler = CEKIRDEK_SABLON # Varsayılan
            try:
                # Eğer farklı şablonlar kullanıldıysa sistemi geliştirecek altyapı
                pass
            except: pass

            st.markdown("---")
            
            # 3 FARKLI PROFESYONEL GÖRÜNÜM
            gorunum = st.radio("Lütfen Görüntülemek İstediğiniz Rapor Türünü Seçin:", [
                "🏢 1. Resmi İdare Not Çizelgesi (Matris Görünüm)", 
                "📝 2. Geniş Görünüm (Tüm Detaylar ve AI Yorumları)",
                "📊 3. Dar Görünüm (Sadece İsim ve Toplam Puan)"
            ], horizontal=False)
            
            # =========================================================
            # 1. GÖRÜNÜM: İSTENEN İDARE NOT ÇİZELGESİ (MATRİS)
            # =========================================================
            if gorunum == "🏢 1. Resmi İdare Not Çizelgesi (Matris Görünüm)":
                st.info(f"💡 {r_sinif} Sınıfı için Okul İdaresine teslim edilecek, numara sırasına dizilmiş puan dağılım listesi.")
                
                # İdareye özel DataFrame oluşturma
                idare_df = pd.DataFrame()
                
                # Okul No'yu sayısal sıralamak için geçici dönüştürme yapıyoruz
                df_yazdir_sirali = df_yazdir.copy()
                df_yazdir_sirali['Siralama_No'] = pd.to_numeric(df_yazdir_sirali['Okul No'], errors='coerce').fillna(9999)
                df_yazdir_sirali = df_yazdir_sirali.sort_values(by='Siralama_No').drop(columns=['Siralama_No'])
                
                idare_df["Okul No"] = df_yazdir_sirali["Okul No"]
                idare_df["Öğrenci Adı Soyadı"] = df_yazdir_sirali["Öğrenci Adı Soyadı"]
                
                # Dinamik Sütun Başlıkları (Kriter Adı + Parantez İçinde Max Puan)
                for k in aktif_kriterler:
                    sutun_basligi = f"{k['baslik']} (Max: {k['max']})"
                    idare_df[sutun_basligi] = df_yazdir_sirali[f"{k['baslik']} Puanı"]
                
                idare_df["TOPLAM PUAN"] = df_yazdir_sirali["Toplam Puan"]
                
                # Tabloyu Ekrana Bas
                st.dataframe(idare_df, use_container_width=True, hide_index=True)
                
# İdare Excel'i Çıktısı
                output_idare = io.BytesIO()
                with pd.ExcelWriter(output_idare, engine='xlsxwriter') as writer:
                    # Sınıf adındaki "/" işaretini "_" ile değiştiriyoruz (Excel yasağını aşmak için)
                    guvenli_sinif = r_sinif.replace('/', '_').replace('\\', '_')
                    sheet_ismi = f'{guvenli_sinif}_Idare'[:31] # Excel sheet ismi max 31 karakter olabilir
                    
                    idare_df.to_excel(writer, index=False, sheet_name=sheet_ismi)
                    worksheet = writer.sheets[sheet_ismi]
                    worksheet.set_column(0, 0, 10) # Okul No genişliği
                    worksheet.set_column(1, 1, 25) # İsim genişliği
                    worksheet.set_column(2, len(aktif_kriterler)+2, 18) # Kriter sütunları genişliği
                
                st.download_button(
                    "🟢 İdare Not Çizelgesini İndir (Excel)", 
                    data=output_idare.getvalue(), 
                    file_name=f"{guvenli_sinif}_Resmi_Not_Cizelgesi.xlsx", 
                    mime="application/vnd.ms-excel", 
                    use_container_width=True
                )

            # =========================================================
            # 2. GÖRÜNÜM: GENİŞ LİSTE
            # =========================================================
            elif gorunum == "📝 2. Geniş Görünüm (Tüm Detaylar ve AI Yorumları)":
                st.dataframe(df_yazdir, use_container_width=True)

            # =========================================================
            # 3. GÖRÜNÜM: DAR LİSTE
            # =========================================================
            else:
                dar_sutunlar = ['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Ders', 'Toplam Puan']
                st.dataframe(df_yazdir[dar_sutunlar].sort_values(by="Okul No"), use_container_width=True, hide_index=True)
                
            st.markdown("---")
            st.markdown("#### 🖨️ Öğrenci & Veli PDF Karneleri")
            if not df_yazdir.empty:
                d_ad = k_bilgi.get("ad", "Öğretmen")
                d_brans = df_yazdir.iloc[0].get("Ders", "Genel")
                html_cikti = toplu_karne_html_dosyasi_uret(df_yazdir, d_ad, d_brans, aktif_kriterler)
                st.download_button("🖨️ Sınıfın Renkli Veli Karnelerini İndir (HTML/PDF)", html_cikti, file_name=f"{r_sinif.replace('/', '_')}_Veli_Karneleri.html", mime="text/html", use_container_width=True)
# --- SEKME: AKILLI KARNE GÖRÜŞÜ (YENİ MODÜL) ---
    sekme_karne = sekmeler[4] if rol == "admin" else sekmeler[3]
    with sekme_karne:
        st.markdown("### 📝 Yapay Zeka Destekli Karne Görüşü Yazıcı")
        st.info("💡 E-Okul veya kendi Excel/CSV listenizi (Öğrenci Adı, Sınıf, Okul No ve Ders Notlarını içeren) buraya yükleyin. AI tüm notlara bakarak öğrenciye özel görüş yazar.")
        
        # Dosya Yükleme Alanı (.xls ve .xlsx destekli)
        karne_dosya = st.file_uploader("Öğrenci Not Listesini Yükleyin (CSV veya Excel)", type=['csv', 'xlsx', 'xls'])
        
        if karne_dosya:
            if "karne_df" not in st.session_state or st.session_state.get("son_yuklenen_karne") != karne_dosya.name:
                try:
                    if karne_dosya.name.endswith('.csv'):
                        k_df = pd.read_csv(karne_dosya, sep=None, engine='python')
                    else:
                        k_df = pd.read_excel(karne_dosya)
                    
                    if "AI_Karne_Gorusu" not in k_df.columns:
                        k_df["AI_Karne_Gorusu"] = ""
                    
                    st.session_state["karne_df"] = k_df
                    st.session_state["son_yuklenen_karne"] = karne_dosya.name
                except Exception as e:
                    st.error(f"Dosya okuma hatası: {e}")
            
            if "karne_df" in st.session_state:
                k_df = st.session_state["karne_df"]
                
                # Sütunları dinamik tespit et (Büyük/küçük harf duyarsız)
                kolonlar = k_df.columns.tolist()
                ad_kolonu = next((col for col in kolonlar if "ad" in str(col).lower() and "soyad" in str(col).lower()), kolonlar[2] if len(kolonlar)>2 else kolonlar[0])
                sinif_kolonu = next((col for col in kolonlar if "sınıf" in str(col).lower() or "sinif" in str(col).lower()), kolonlar[0])
                no_kolonu = next((col for col in kolonlar if "no" in str(col).lower()), kolonlar[1] if len(kolonlar)>1 else kolonlar[0])
                
                # Ders kolonlarını ayıkla (Öğrenci bilgileri haricindeki her şey ders notu kabul edilir)
                ders_kolonlari = [col for col in kolonlar if col not in [ad_kolonu, sinif_kolonu, no_kolonu, "AI_Karne_Gorusu"]]
                
                st.success(f"✅ Dosya başarıyla yüklendi ve {len(ders_kolonlari)} farklı ders tespit edildi!")
                
                # NOT: 4. Bölüm kodları tam bu satırın altına gelecek.
# ==========================================
# 12. ANA ÇALIŞTIRMA MODÜLÜ
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df = veri_yukle()

    st.markdown("""
    <div class="hero-header">
      <div class="hero-title">🏫 Proje ve Karne Yönetim Sistemi</div>
      <div class="hero-subtitle">Yapay Zeka Destekli, Çoklu Ders ve Dinamik Şablon Mimarisi</div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2 = st.tabs(["🎓 Öğrenci Girişi (Karneler)", "👨‍🏫 Yönetim ve Öğretmen Paneli"])
    with t1: ogrenci_paneli(df, ayarlar)
    with t2:
        if "giris_yapti" not in st.session_state: st.session_state["giris_yapti"] = False
        if not st.session_state["giris_yapti"]: giris_paneli(ayarlar)
        else: yonetim_paneli(df, ayarlar)

if __name__ == "__main__":
    main()
