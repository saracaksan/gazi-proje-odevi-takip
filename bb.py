import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import json
import time
import requests

# ==========================================
# 1. BÖLÜM: KURULUMLAR VE TASARIM
# ==========================================
st.set_page_config(page_title="Gazi Ortaokulu | Proje Sistemi", page_icon="🏫", layout="wide", initial_sidebar_state="collapsed")

# ─── ÖZEL CSS TASARIM ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2044 100%); min-height: 100vh; }
.hero-header { background: linear-gradient(135deg, #1e40af, #3b82f6, #60a5fa); border-radius: 20px; padding: 32px 40px; margin-bottom: 28px; text-align: center; box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4); position: relative; overflow: hidden; }
.hero-title { font-family: 'Nunito', sans-serif; font-size: 2.4rem; font-weight: 900; color: white; margin: 0 0 6px 0; text-shadow: 0 2px 10px rgba(0,0,0,0.3); letter-spacing: -0.5px; }
.hero-subtitle { font-size: 1.05rem; color: rgba(255,255,255,0.85); margin: 0; font-weight: 500; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 6px; border: 1px solid rgba(255,255,255,0.1); gap: 4px; margin-bottom: 20px; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: transparent; border-radius: 12px; color: rgba(255,255,255,0.6); font-weight: 600; font-size: 0.95rem; padding: 10px 24px; border: none; transition: all 0.25s ease; }
[data-testid="stTabs"] [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.08); color: white; }
[data-testid="stTabs"] [aria-selected="true"] { background: linear-gradient(135deg, #2563eb, #3b82f6) !important; color: white !important; box-shadow: 0 4px 16px rgba(37, 99, 235, 0.5); }
.glass-card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 24px; margin-bottom: 18px; backdrop-filter: blur(12px); }
.metric-card { background: linear-gradient(135deg, rgba(37,99,235,0.3), rgba(59,130,246,0.15)); border: 1px solid rgba(96,165,250,0.3); border-radius: 16px; padding: 20px; text-align: center; }
.metric-card .metric-value { font-family: 'Nunito', sans-serif; font-size: 2.4rem; font-weight: 900; color: #60a5fa; line-height: 1; }
.metric-card .metric-label { font-size: 0.8rem; color: rgba(255,255,255,0.55); margin-top: 6px; font-weight: 600; text-transform: uppercase; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { background-color: #1e293b !important; border: 1px solid #3b82f6 !important; border-radius: 10px !important; color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label { color: rgba(255,255,255,0.75) !important; font-weight: 600 !important; font-size: 0.85rem !important; }
.stButton > button { background: linear-gradient(135deg, #2563eb, #3b82f6) !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 12px 24px !important; font-weight: 700 !important; font-family: 'Nunito', sans-serif !important; transition: all 0.25s ease !important; box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4) !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(37, 99, 235, 0.6) !important; background: linear-gradient(135deg, #1d4ed8, #2563eb) !important; }
.stDownloadButton > button { background: linear-gradient(135deg, #059669, #10b981) !important; }
.stSuccess { background: rgba(16, 185, 129, 0.15) !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; border-radius: 12px !important; color: white !important;}
.stError { background: rgba(239, 68, 68, 0.15) !important; border: 1px solid rgba(239, 68, 68, 0.3) !important; border-radius: 12px !important; color: white !important;}
.stWarning { background: rgba(245, 158, 11, 0.15) !important; border: 1px solid rgba(245, 158, 11, 0.3) !important; border-radius: 12px !important; color: white !important;}
.stInfo { background: rgba(59, 130, 246, 0.15) !important; border: 1px solid rgba(59, 130, 246, 0.3) !important; border-radius: 12px !important; color: white !important;}
.stDataFrame { background: rgba(255,255,255,0.04) !important; border-radius: 14px !important; overflow: hidden !important; }
.puan-bar-wrapper { width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden; margin-top: 4px; }
.puan-bar-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, #3b82f6, #60a5fa); transition: width 0.6s ease; }
.kriter-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 16px 20px; margin-bottom: 14px; }
.kriter-baslik { font-family: 'Nunito', sans-serif; font-weight: 800; color: #93c5fd; font-size: 0.95rem; margin-bottom: 4px; }
.kriter-aciklama { color: rgba(255,255,255,0.45); font-size: 0.78rem; font-style: italic; }
.ai-btn > button { background: linear-gradient(135deg, #7c3aed, #a855f7) !important; box-shadow: 0 4px 20px rgba(124, 58, 237, 0.5) !important; }
.kaydet-btn > button { background: linear-gradient(135deg, #059669, #10b981) !important; box-shadow: 0 4px 20px rgba(5, 150, 105, 0.5) !important; }
.toplam-badge { background: linear-gradient(135deg, #dc2626, #ef4444); color: white; font-family: 'Nunito', sans-serif; font-size: 2rem; font-weight: 900; border-radius: 16px; padding: 16px 32px; text-align: center; box-shadow: 0 8px 24px rgba(220, 38, 38, 0.4); display: inline-block; min-width: 120px; }
.custom-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); margin: 20px 0; }
div[data-baseweb="select"] > div { background-color: #1e293b !important; border: 1px solid #3b82f6 !important; border-radius: 10px !important; color: white !important; }
div[data-baseweb="popover"], ul[data-baseweb="menu"] { background-color: #1e293b !important; border-radius: 10px !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# VERİTABANI, AI VE SABİTLER
# ==========================================
DATA_FILE = "veritabani.csv"
OGRETMENLER_FILE = "ogretmenler.json"

try: API_KEY = st.secrets["API_KEY"]
except: API_KEY = "AIzaSyDR59-y8bOekDJBHjSN9vvFfjhWXQfPRUM"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

KRITERLER = [
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu",  "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi ve konu hakimiyeti."},
    {"id": "k2", "baslik": "Düzen ve Tertip",               "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli hazırlanmış olması. Kağıt kullanımının özeni."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler veya açıklamalar eklenmesi."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum",        "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi."},
    {"id": "k5", "baslik": "Zamanında Teslim",            "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte (26 Nisan 2026) teslim edilmesi."},
]

# Çoklu Öğretmen Desteği İçin Yeni Sütun: 'Öğretmen_Kullanıcı'
GEREKLI_SUTUNLAR = ['S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', '1. Dönem Puanı', 'Proje', 'Durum', 'Öğretmen_Kullanıcı']
for _k in KRITERLER:
    GEREKLI_SUTUNLAR.append(f"{_k['baslik']} Puanı")
    GEREKLI_SUTUNLAR.append(f"{_k['baslik']} Açıklaması")
GEREKLI_SUTUNLAR.extend(['Genel Değerlendirme Yorumu', 'Toplam Puan'])

# ==========================================
# VERİ FONKSİYONLARI
# ==========================================
def ogretmenleri_yukle():
    if os.path.exists(OGRETMENLER_FILE):
        with open(OGRETMENLER_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def ogretmenleri_kaydet(data):
    with open(OGRETMENLER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=0)
def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype={"Okul No": str})
            df.dropna(subset=['Okul No'], inplace=True)
            df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
            for s in GEREKLI_SUTUNLAR:
                if s not in df.columns:
                    df[s] = 'admin' if s == 'Öğretmen_Kullanıcı' else None
            return df
        except Exception: return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
    return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

def veriyi_kaydet(df):
    df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()

def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', '1. Dönem Puanı', 'Proje', 'Durum'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Sablonu')
        for col_num in range(len(sablon_df.columns)):
            writer.sheets['Ogrenci_Sablonu'].set_column(col_num, col_num, 22)
    return output.getvalue()

def puan_renk(puan, max_puan):
    oran = puan / max_puan if max_puan > 0 else 0
    return "#10b981" if oran >= 0.85 else ("#f59e0b" if oran >= 0.60 else "#ef4444")

# ==========================================
# ÇIKTI FONKSİYONLARI (PDF / HTML)
# ==========================================
def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans):
    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Proje Karneleri</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #f1f5f9; }}
  .page {{ background: white; width: 210mm; margin: 10mm auto; padding: 15mm; border-radius: 4px; page-break-after: always; }}
  table {{ width: 100%; border-collapse: collapse; margin-top:15px; }}
  th {{ background: #1e3a8a; color: white; padding: 10px; font-size: 13px; text-align: left; }}
  td {{ padding: 10px; font-size: 13px; border-bottom: 1px solid #e2e8f0; }}
  .header {{ background: linear-gradient(135deg,#1e3a8a,#2563eb); color:white; padding:15px; border-radius:8px; margin-bottom:15px; }}
  .yorum {{ background:#eff6ff; border-left:3px solid #3b82f6; padding:12px; margin-top:15px; font-size:13px; color:#1e40af; }}
  @media print {{ body{{background:white;}} .page{{margin:0; width:100%; box-shadow:none;}} }}
</style></head><body>"""
    
    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam = int(pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce') or 0)
        renk = "#10b981" if toplam >= 85 else ("#f59e0b" if toplam >= 60 else "#ef4444")
        html += f"""<div class="page">
  <div class="header">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <h3>Gazi Ortaokulu - {ogrt_brans} Proje Karnesi</h3>
      <div style="background:white;color:{renk};font-size:24px;font-weight:bold;padding:5px 15px;border-radius:5px;">{toplam}/100</div>
    </div>
  </div>
  <p>👤 <b>Öğrenci:</b> {b.get('Öğrenci Adı Soyadı','')} | 🏫 <b>Sınıf:</b> {b.get('Sınıf','')} | 🔢 <b>No:</b> {b.get('Okul No','')}</p>
  <table><tr><th>Kriter</th><th style="width:50px;">Max</th><th style="width:50px;">Puan</th><th>Değerlendirme</th></tr>"""
        for k in KRITERLER:
            p = int(pd.to_numeric(b.get(f"{k['baslik']} Puanı", 0), errors='coerce') or 0)
            a = b.get(f"{k['baslik']} Açıklaması", "-")
            html += f"<tr><td><b>{k['baslik']}</b></td><td style='text-align:center;'>{k['max']}</td><td style='text-align:center;font-weight:bold;'>{p}</td><td>{a}</td></tr>"
        genel = str(b.get('Genel Değerlendirme Yorumu', '')) or "Değerlendirme girilmedi."
        html += f"""</table><div class="yorum"><b>💬 Genel Değerlendirme:</b><br>{genel}</div>
  <div style="text-align:right; margin-top:30px;"><b>{ogrt_ad}</b><br>{ogrt_brans} Öğretmeni</div></div>"""
    html += "</body></html>"
    return html

def ai_degerlendirme_yap(bilgi_dict, ham_metin, puanlar, ogrt_ad, ogrt_brans):
    puan_ozeti = "\n".join([f"  - {k['baslik']}: {puanlar.get(k['id'], 0)}/{k['max']}" for k in KRITERLER])
    prompt = f"""Sen Gazi Ortaokulu'nda görev yapan deneyimli ve motive edici bir {ogrt_brans.lower()} öğretmenisin. Adın {ogrt_ad}.
Öğrencinin puanları:
{puan_ozeti}
Öğretmen Özel Notu: "{ham_metin if ham_metin.strip() else 'Yok. Sadece puanlara göre yorum yap.'}"

GÖREV:
1) Öğretmen notunu da harmanlayarak her kriter için öğrenciye doğrudan hitap eden (Sen dili), eksikleri şefkatle belirten motive edici 1 cümlelik JSON çıktı üret.
2) "genel" kısmında önce {ogrt_brans.lower()} dersinin günlük hayattaki öneminden bahset, sonra öğrenciyi motive et.
SADECE GEÇERLİ JSON VER:
{{ "k1": "...", "k2": "...", "k3": "...", "k4": "...", "k5": "...", "genel": "..." }}"""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    response.raise_for_status()
    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw)

# ==========================================
# ÖĞRENCİ PANELİ
# ==========================================
def ogrenci_paneli(df):
    st.markdown("""<div style="text-align:center; margin-bottom:28px;"><div style="font-size:3.5rem; margin-bottom:8px;">🎓</div>
      <div style="font-size:1.5rem; font-weight:800; color:white;">Proje Sonuç Sorgulama</div></div>""", unsafe_allow_html=True)
    if df.empty:
        st.warning("⚠️ Sisteme henüz veri yüklenmemiştir.")
        return
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        sinif = st.selectbox("🏫 Sınıfınız", ["— Seçiniz —"] + sorted(df['Sınıf'].dropna().unique().tolist()))
        okul_no = st.text_input("🔢 Okul Numaranız")
        sorgula = st.button("🔍 Sonucumu Göster", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if sorgula:
        if sinif == "— Seçiniz —" or not okul_no.strip():
            st.error("❌ Sınıf ve numara zorunludur.")
        else:
            ogrenci = df[(df['Sınıf'] == sinif) & (df['Okul No'] == okul_no.strip())]
            if ogrenci.empty:
                st.error("❌ Kayıt bulunamadı.")
            else:
                bilgi = ogrenci.iloc[0]
                
                # İlgili öğretmeni bulma
                hoca_kullanici = bilgi.get('Öğretmen_Kullanıcı', 'admin')
                if hoca_kullanici == 'admin':
                    ogrt_ad, ogrt_brans = "Sıraç AKSAN", "Matematik"
                else:
                    ogretmenler = ogretmenleri_yukle()
                    ogrt_ad = ogretmenler.get(hoca_kullanici, {}).get("ad", "Öğretmen")
                    ogrt_brans = ogretmenler.get(hoca_kullanici, {}).get("brans", "Ders")

                st.success(f"✅ Hoş geldiniz, {bilgi.get('Öğrenci Adı Soyadı', '')}!")
                st.info(f"Proje değerlendirmeniz {ogrt_brans} öğretmeniniz {ogrt_ad} tarafından yapılmıştır.")
                
                tek_df = pd.DataFrame([bilgi])
                html_cikti = toplu_karne_html_dosyasi_uret(tek_df, ogrt_ad, ogrt_brans)
                
                c_bos1, c_indir, c_bos2 = st.columns([1, 2, 1])
                with c_indir:
                    st.download_button("🖨️ Detaylı Karnemi İndir (PDF/HTML)", data=html_cikti, 
                                       file_name=f"{okul_no}_Karne.html", mime="text/html", use_container_width=True)
                                       # ==========================================
# YÖNETİCİ (ADMIN) PANELİ
# ==========================================
def admin_paneli(df):
    st.markdown("### 👑 Okul Yöneticisi Paneli (Admin)")
    if st.button("🚪 Admin Çıkışı"):
        st.session_state["aktif_kullanici"] = None
        st.rerun()
        
    tab1, tab2 = st.tabs(["👨‍🏫 Öğretmen Yönetimi", "📊 Tüm Okul Raporu"])
    
    with tab1:
        st.markdown("#### ➕ Sisteme Yeni Öğretmen Ekle")
        ogretmenler = ogretmenleri_yukle()
        
        with st.form("yeni_ogretmen_ekle"):
            c1, c2 = st.columns(2)
            y_user = c1.text_input("Kullanıcı Adı (Sisteme giriş için, örn: ahmet_hoca)")
            y_pass = c2.text_input("Şifre", type="password")
            y_ad = c1.text_input("Öğretmen Adı Soyadı")
            y_brans = c2.text_input("Branşı (Örn: Matematik)")
            
            if st.form_submit_button("Öğretmen Ekle"):
                if not y_user or not y_pass or not y_ad or not y_brans:
                    st.error("Tüm alanları doldurun!")
                elif y_user in ogretmenler or y_user == "admin":
                    st.error("Bu kullanıcı adı zaten var!")
                else:
                    ogretmenler[y_user] = {"sifre": y_pass, "ad": y_ad, "brans": y_brans}
                    ogretmenleri_kaydet(ogretmenler)
                    st.success(f"{y_ad} sisteme başarıyla eklendi!")
                    time.sleep(1)
                    st.rerun()
                    
        st.markdown("---")
        st.markdown("#### 📋 Sistemdeki Öğretmenler")
        if ogretmenler:
            for k_adi, d in ogretmenler.items():
                st.info(f"**Kullanıcı Adı:** {k_adi} | **Adı:** {d['ad']} | **Branş:** {d['brans']}")
                if st.button(f"🗑️ {k_adi} Sil", key=f"sil_{k_adi}"):
                    del ogretmenler[k_adi]
                    ogretmenleri_kaydet(ogretmenler)
                    st.success("Öğretmen silindi.")
                    time.sleep(1)
                    st.rerun()
        else:
            st.write("Sistemde admin dışında öğretmen yok.")

    with tab2:
        st.markdown("#### 📊 Tüm Okul Proje İstatistikleri")
        st.write("Yönetici olarak tüm öğretmenlerin girdiği kayıtları görebilirsiniz.")
        st.dataframe(df, use_container_width=True)

# ==========================================
# ÖĞRETMEN PANELİ
# ==========================================
def ogretmen_paneli(df, k_adi, o_ad, o_brans):
    st.markdown(f"### 👋 Hoş Geldiniz, {o_ad} ({o_brans} Öğretmeni)")
    if st.button("🚪 Çıkış Yap"):
        st.session_state["aktif_kullanici"] = None
        st.rerun()
        
    # Öğretmenin SADECE kendi öğrencilerini görmesi için filtreleme!
    # Eğer eski kayıtlarsa (admin), onları admin paneline bıraktık.
    df_hoca = df[df['Öğretmen_Kullanıcı'] == k_adi].copy()

    otab1, otab2, otab3, otab4 = st.tabs(["📂 Veri Yükle", "👤 Öğrenci İşlemleri", "🤖 Puanlama & AI", "📊 Rapor & Çıktı"])

    with otab1:
        st.markdown("#### 📥 Şablon İndirme ve Veri Yükleme")
        st.download_button("⬇️ Boş Şablon İndir", data=bos_sablon_olustur(), file_name="Ogrenci_Veri.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        yuklenen = st.file_uploader("Öğrenci Listenizi Yükleyin", type=['xlsx', 'csv'])
        if yuklenen and st.button("💾 Yükle"):
            try:
                y_df = pd.read_csv(yuklenen, dtype={"Okul No": str}) if yuklenen.name.endswith('.csv') else pd.read_excel(yuklenen, dtype={"Okul No": str})
                y_df['Okul No'] = y_df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
                y_df.dropna(subset=['Okul No'], inplace=True)
                
                # Sistemin genelinde (diğer hocalarda) var mı kontrol et
                mevcut_tumu = df['Okul No'].tolist()
                eklenecek = y_df[~y_df['Okul No'].isin(mevcut_tumu)].copy()
                
                if eklenecek.empty:
                    st.warning("⚠️ Bu öğrenciler sistemde başka bir öğretmende veya sizde zaten kayıtlı! Çift kayıt engellendi.")
                else:
                    eklenecek['Öğretmen_Kullanıcı'] = k_adi
                    for s in GEREKLI_SUTUNLAR:
                        if s not in eklenecek.columns: eklenecek[s] = None
                    df = pd.concat([df, eklenecek], ignore_index=True)
                    veriyi_kaydet(df)
                    st.success(f"✅ {len(eklenecek)} öğrenci size tanımlandı!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Hata: {e}")

    with otab2:
        st.markdown("#### 👤 Öğrenci Ekle / Düzenle / Sil")
        islem = st.radio("İşlem:", ["➕ Yeni Ekle", "✏️ Düzenle", "🗑️ Sil"], horizontal=True, label_visibility="collapsed")
        
        if islem == "➕ Yeni Ekle":
            with st.form("yeni_form"):
                c1, c2 = st.columns(2)
                no = c1.text_input("Okul Numarası *")
                ad = c2.text_input("Ad Soyad *")
                sinif = c1.text_input("Sınıf *")
                durum = c2.selectbox("Durum", ["Zorunlu", "Gönüllü", "Proje Üst"])
                if st.form_submit_button("Kaydet"):
                    if not no or not ad or not sinif:
                        st.error("Yıldızlı alanları doldurun!")
                    elif no.strip() in df['Okul No'].tolist():
                        st.error("Bu okul numarası zaten sistemde kayıtlı!")
                    else:
                        y_veri = {col: None for col in GEREKLI_SUTUNLAR}
                        y_veri.update({'Okul No': no.strip(), 'Öğrenci Adı Soyadı': ad.strip(), 'Sınıf': sinif.strip(), 'Durum': durum, 'Öğretmen_Kullanıcı': k_adi})
                        df.loc[len(df)] = y_veri
                        veriyi_kaydet(df)
                        st.success("Eklendi!")
                        time.sleep(1)
                        st.rerun()
                        
        elif islem == "✏️ Düzenle":
            if not df_hoca.empty:
                s_ogr = st.selectbox("Seç:", ["Seçiniz"] + df_hoca.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist())
                if s_ogr != "Seçiniz":
                    ogr_no = s_ogr.split(" - ")[0]
                    # Ana df üzerindeki gerçek index'i bul
                    idx = df.index[df['Okul No'] == ogr_no].tolist()[0]
                    with st.form("duz_form"):
                        c1, c2 = st.columns(2)
                        gun_ad = c1.text_input("Ad", df.at[idx, 'Öğrenci Adı Soyadı'])
                        gun_sinif = c2.text_input("Sınıf", df.at[idx, 'Sınıf'])
                        if st.form_submit_button("Güncelle"):
                            df.at[idx, 'Öğrenci Adı Soyadı'] = gun_ad
                            df.at[idx, 'Sınıf'] = gun_sinif
                            veriyi_kaydet(df)
                            st.success("Güncellendi!")
                            time.sleep(1)
                            st.rerun()
                            
        elif islem == "🗑️ Sil":
            if not df_hoca.empty:
                s_ogr = st.selectbox("Silinecek Öğrenci:", ["Seçiniz"] + df_hoca.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist())
                if s_ogr != "Seçiniz":
                    if st.button("🗑️ Kalıcı Olarak Sil"):
                        ogr_no = s_ogr.split(" - ")[0]
                        df = df[df['Okul No'] != ogr_no].reset_index(drop=True)
                        veriyi_kaydet(df)
                        st.success("Silindi!")
                        time.sleep(1)
                        st.rerun()

    with otab3:
        st.markdown("#### 🤖 Puanlama & Yapay Zeka Değerlendirmesi")
        if df_hoca.empty:
            st.info("Listenizde öğrenci yok.")
        else:
            s_ogr = st.selectbox("Değerlendirilecek Öğrenci:", ["Seçiniz"] + df_hoca.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist())
            if s_ogr != "Seçiniz":
                ogr_no = s_ogr.split(" - ")[0]
                idx = df.index[df['Okul No'] == ogr_no].tolist()[0]
                bilgi = df.iloc[idx]
                
                puanlar = {}
                toplam_anlik = 0
                for k in KRITERLER:
                    pk = f"puan_{idx}_{k['id']}"
                    ak = f"aciklama_{idx}_{k['id']}"
                    if pk not in st.session_state:
                        db_p = df.at[idx, f"{k['baslik']} Puanı"]
                        st.session_state[pk] = int(pd.to_numeric(db_p, errors='coerce')) if pd.notna(db_p) else 0
                    if ak not in st.session_state:
                        db_a = df.at[idx, f"{k['baslik']} Açıklaması"]
                        st.session_state[ak] = str(db_a) if pd.notna(db_a) else ""
                        
                    c1, c2 = st.columns([1, 4])
                    st.session_state[pk] = c1.number_input(f"{k['baslik']} (Max:{k['max']})", 0, k['max'], st.session_state[pk])
                    toplam_anlik += st.session_state[pk]
                    st.session_state[ak] = c2.text_input(f"Açıklama:", value=st.session_state[ak], key=f"t_{ak}")
                
                gk = f"genel_{idx}"
                if gk not in st.session_state:
                    db_g = df.at[idx, 'Genel Değerlendirme Yorumu']
                    st.session_state[gk] = str(db_g) if pd.notna(db_g) else ""
                st.session_state[gk] = st.text_area("Genel Yorum:", value=st.session_state[gk], key=f"t_{gk}")
                
                ham_metin = st.text_area("💡 Yapay Zekaya Özel Notunuz:")
                
                c_ai, c_sav = st.columns(2)
                with c_ai:
                    if st.button("✨ Yapay Zeka Doldursun"):
                        with st.spinner("AI Değerlendiriyor..."):
                            try:
                                json_data = ai_degerlendirme_yap(bilgi.to_dict(), ham_metin, {k['id']:st.session_state[f"puan_{idx}_{k['id']}"] for k in KRITERLER}, o_ad, o_brans)
                                for k in KRITERLER:
                                    if k['id'] in json_data: st.session_state[f"aciklama_{idx}_{k['id']}"] = json_data[k['id']]
                                if "genel" in json_data: st.session_state[gk] = json_data["genel"]
                                st.rerun()
                            except Exception as e: st.error(f"AI Hatası: {e}")
                with c_sav:
                    if st.button("💾 Kaydet"):
                        for k in KRITERLER:
                            df.at[idx, f"{k['baslik']} Puanı"] = st.session_state[f"puan_{idx}_{k['id']}"]
                            df.at[idx, f"{k['baslik']} Açıklaması"] = st.session_state[f"aciklama_{idx}_{k['id']}"]
                        df.at[idx, 'Genel Değerlendirme Yorumu'] = st.session_state[gk]
                        df.at[idx, 'Toplam Puan'] = toplam_anlik
                        veriyi_kaydet(df)
                        st.success("Kayıt Başarılı!")

    with otab4:
        st.markdown("#### 📊 Öğrencilerinizin Raporları")
        if df_hoca.empty: st.info("Veri yok.")
        else:
            st.dataframe(df_hoca[['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Toplam Puan']], hide_index=True)
            
            st.markdown("##### 📥 Çıktı Al (PDF / WhatsApp)")
            secili_sinif = st.selectbox("Çıktı Alınacak Sınıfı Seçin:", sorted(df_hoca['Sınıf'].dropna().unique().tolist()))
            if st.button("🖨️ Bu Sınıfın Karnelerini Hazırla"):
                cikti_df = df_hoca[df_hoca['Sınıf'] == secili_sinif]
                html_karne = toplu_karne_html_dosyasi_uret(cikti_df, o_ad, o_brans)
                st.download_button("⬇️ İndir ve Yazdır", data=html_karne, file_name=f"{secili_sinif.replace('/','_')}_Karneler.html", mime="text/html")

# ==========================================
# GİRİŞ KONTROLÜ VE ANA YAPI
# ==========================================
def panel_giris(df):
    if "aktif_kullanici" not in st.session_state:
        st.session_state["aktif_kullanici"] = None
        st.session_state["is_admin"] = False
        st.session_state["ogretmen_adi"] = ""
        st.session_state["ogretmen_bransi"] = ""

    if st.session_state["aktif_kullanici"] is None:
        st.markdown('<div class="glass-card" style="max-width:500px; margin: 0 auto; text-align:center;">', unsafe_allow_html=True)
        st.markdown("### 🔐 Öğretmen / Yönetici Girişi")
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap", use_container_width=True):
            if kadi == "admin" and sifre == "Sarac.47":
                st.session_state["aktif_kullanici"] = "admin"
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                ogretmenler = ogretmenleri_yukle()
                if kadi in ogretmenler and ogretmenler[kadi]["sifre"] == sifre:
                    st.session_state["aktif_kullanici"] = kadi
                    st.session_state["is_admin"] = False
                    st.session_state["ogretmen_adi"] = ogretmenler[kadi]["ad"]
                    st.session_state["ogretmen_bransi"] = ogretmenler[kadi]["brans"]
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        if st.session_state["is_admin"]:
            admin_paneli(df)
        else:
            ogretmen_paneli(df, st.session_state["aktif_kullanici"], st.session_state["ogretmen_adi"], st.session_state["ogretmen_bransi"])

def main():
    st.markdown("""<div class="hero-header"><div class="hero-title">🏫 Gazi Ortaokulu</div>
      <div class="hero-subtitle">Proje Değerlendirme & Okul Otomasyon Sistemi</div></div>""", unsafe_allow_html=True)

    df = veri_yukle()
    tab1, tab2 = st.tabs(["🎓 Öğrenci Ekranı", "👨‍🏫 Öğretmen / Admin Ekranı"])
    with tab1: ogrenci_paneli(df)
    with tab2: panel_giris(df)

if __name__ == "__main__":
    main()
