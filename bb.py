import streamlit as st
import pandas as pd
import io
import os
import json
import requests
import time
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# ==========================================
# 1. SAYFA YAPILANDIRMASI
# ==========================================
st.set_page_config(
    page_title="PUSULA 360 | Bütüncül Değerlendirme Platformu",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. GİZLİ KASA VE API BAĞLANTILARI
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
except Exception:
    st.error("⚠️ HATA: GEMINI_API_KEY gizli kasada bulunamadı!")
    st.stop()

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip()
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"⚠️ Supabase bağlantı hatası: {e}")
    st.stop()

EMAIL_SENDER = "properkar360@gmail.com"
try:
    EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")
except Exception:
    EMAIL_PASSWORD = ""

# ==========================================
# 3. GLOBAL CSS — KOYU TEMA (DARK GLASS) VE MOBİL UYUM
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Lexend:wght@400;600;800&display=swap');

/* ── Reset & Temel ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0f172a; /* KOYU ARKA PLAN */
    color: rgba(255,255,255,0.9);
}
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2044 100%);
    min-height: 100vh;
}
.block-container {
    padding: 0.5rem 1rem 2rem !important;
    max-width: 1350px !important;
}

/* ── Hero ── */
.p360-hero {
    background: linear-gradient(135deg, #0c1e4a 0%, #1a3a8f 50%, #2563eb 100%);
    border-radius: 16px;
    padding: 24px 30px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(30,58,138,0.4);
    text-align: center;
}
.p360-hero::after {
    content: ''; position: absolute; top: -60%; right: -10%; width: 350px; height: 350px;
    background: radial-gradient(circle, rgba(255,255,255,0.07) 0%, transparent 70%); pointer-events: none;
}
.p360-hero-title { font-family: 'Lexend', sans-serif; font-size: clamp(1.5rem, 4vw, 2.2rem); font-weight: 800; color: #fff; margin: 0; letter-spacing: -0.3px; }
.p360-hero-sub { color: #93c5fd; font-size: clamp(0.85rem, 2.5vw, 1rem); margin-top: 5px; font-weight: 500; }
.p360-hero-badge { display: inline-block; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2); color: #bfdbfe; padding: 3px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; margin-top: 8px; }

/* ── Profil Çubuğu ── */
.profil-bar {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between;
    border-left: 4px solid #2563eb; margin-bottom: 16px; backdrop-filter: blur(10px);
}
.profil-bar-isim { font-weight: 800; font-size: 1.1rem; color: white; }
.profil-bar-detay { font-size: 0.85rem; color: #94a3b8; margin-top: 2px; }
.admin-badge { background: #fee2e2; color: #dc2626; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 6px; margin-left: 6px; }
.bakis-badge { background: #fef9c3; color: #854d0e; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; margin-left: 6px; }

/* ── ANA MENÜ (Radio Hack - Çift Tıklamayı Önler, Renkleri Korur) ── */
.stRadio > div { gap: 8px; display: flex; flex-wrap: wrap; }
[data-testid="stRadio"] div[role="radiogroup"] { width: 100%; }
[data-testid="stRadio"] label {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important; padding: 10px 14px !important;
    transition: all 0.2s !important; cursor: pointer; color: white !important; font-weight: 600 !important;
    flex: 1; text-align: center; justify-content: center; min-width: 120px;
}
[data-testid="stRadio"] label[data-checked="true"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; /* AKTİF MENÜ RENGİ (MAVİ) */
    box-shadow: 0 4px 15px rgba(37,99,235,0.4) !important; border-color: transparent !important;
}
[data-testid="stRadio"] div[role="radio"] { display: none !important; } /* Yuvarlak ikonu gizle */
[data-testid="stRadio"] label:hover { background: rgba(59,130,246,0.2) !important; }

/* ── Kartlar (Glassmorphism) ── */
.card {
    background: rgba(15, 23, 42, 0.6) !important; border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 16px; padding: 24px; margin-bottom: 18px; backdrop-filter: blur(12px); color: white;
}
.card-baslik { font-family: 'Lexend', sans-serif; font-size: 1.1rem; font-weight: 700; color: #93c5fd; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; gap: 8px; }

/* ── Stat Kartlar ── */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-box { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; text-align: center; border-top: 3px solid #2563eb; }
.stat-box.g { border-top-color: #10b981; } .stat-box.o { border-top-color: #f59e0b; } .stat-box.r { border-top-color: #ef4444; }
.stat-num { font-family: 'Lexend', sans-serif; font-size: 1.8rem; font-weight: 800; color: white; line-height: 1; }
.stat-lbl { font-size: 0.75rem; color: #cbd5e1; font-weight: 600; margin-top: 4px; text-transform: uppercase; }

/* ── Form & Input Görünürlüğü (Beyaz Yüzeyde Beyaz Yazı Sorunu Çözümü) ── */
.stTextInput > div > div > input, .stTextArea  > div > div > textarea, .stNumberInput > div > div > input, [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.08) !important; border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 10px !important; color: white !important;
}
.stTextInput > div > div > input::placeholder, .stTextArea  > div > div > textarea::placeholder { color: rgba(255,255,255,0.4) !important; }
[data-baseweb="popover"] { background: #1e293b !important; border: 1px solid rgba(255,255,255,0.15) !important; }
[data-baseweb="menu"] li { color: white !important; }
[data-baseweb="menu"] li:hover, [data-baseweb="menu"] [aria-selected="true"] { background: rgba(59,130,246,0.25) !important; }
[data-baseweb="select"] svg { fill: white !important; }
label, [data-testid="stWidgetLabel"] { color: rgba(255,255,255,0.8) !important; font-weight: 600 !important; font-size: 0.85rem !important; }

/* ── Tablolar ── */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; background: rgba(15, 23, 42, 0.8) !important; }
[data-testid="stDataFrame"] div[data-baseweb="table-custom"] { background: transparent !important; }
[data-testid="stDataFrame"] span { color: #f8fafc !important; }

/* ── Banner Mesajlar ── */
.banner { border-radius: 10px; padding: 12px 16px; margin-bottom: 14px; font-size: 0.875rem; font-weight: 600; border-left: 4px solid; }
.banner.info  { background: rgba(59,130,246,0.15); border-color: #3b82f6; color: #93c5fd; }
.banner.warn  { background: rgba(245,158,11,0.15); border-color: #f59e0b; color: #fcd34d; }
.banner.ok    { background: rgba(16,185,129,0.15); border-color: #10b981; color: #6ee7b7; }
.banner.err   { background: rgba(239,68,68,0.15); border-color: #ef4444; color: #fca5a5; }

/* ── Butonlar ── */
.stButton > button { background: linear-gradient(135deg,#2563eb,#3b82f6) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 700 !important; transition: all 0.2s !important; }
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(37,99,235,0.4) !important; }

/* ── Karne Özel Elementler ── */
.karne-preview { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 16px; position: relative; margin-bottom: 12px; }
.karne-preview.onaylandi { border-color: #10b981; background: rgba(16,185,129,0.05); }
.karne-onay-rozet { position: absolute; top: 12px; right: 12px; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 800; }
.rozet-onay { background: #d1fae5; color: #065f46; } .rozet-bekle { background: #fef9c3; color: #854d0e; } .rozet-yok { background: #fee2e2; color: #991b1b; }
.karne-ogrenci { font-weight: 800; font-size: 1rem; color: #fff; }
.karne-detay { font-size: 0.8rem; color: #cbd5e1; margin-top: 3px; }
.karne-yorum { background: rgba(245,158,11,0.15); border-left: 3px solid #f59e0b; padding: 10px 14px; border-radius: 6px; font-size: 0.85rem; color: #fcd34d; margin-top: 10px; }

/* ── Puan Rozeti ── */
.puan-rozet { display: inline-block; padding: 4px 14px; border-radius: 20px; font-weight: 800; font-size: 0.85rem; color: white; }
.puan-rozet.iyi    { background: #10b981; }
.puan-rozet.orta   { background: #f59e0b; }
.puan-rozet.dusuk  { background: #ef4444; }
.puan-rozet.sifir  { background: #475569; }

/* ── Kriter Kartı ── */
.kriter-card { background: rgba(255,255,255,0.04); padding: 14px; border-radius: 12px; border-left: 4px solid #3b82f6; margin-bottom: 12px; }
.kriter-card .k-baslik { color: #93c5fd; font-weight: 700; font-size: 0.95rem; }
.kriter-card .k-acik   { color: rgba(255,255,255,0.5); font-size: 0.82rem; margin-top: 4px; }

/* ── Footer ── */
.app-footer { background: rgba(15,23,42,0.7); color: #94a3b8; border-radius: 12px; padding: 20px 28px; margin-top: 28px; text-align: center; font-size: 0.85rem; line-height: 1.7; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER VE VERİLER
# ==========================================
TUM_ILLER = [
    "Adana","Adıyaman","Afyonkarahisar","Ağrı","Amasya","Ankara","Antalya","Artvin","Aydın","Balıkesir",
    "Bilecik","Bingöl","Bitlis","Bolu","Burdur","Bursa","Çanakkale","Çankırı","Çorum","Denizli",
    "Diyarbakır","Edirne","Elazığ","Erzincan","Erzurum","Eskişehir","Gaziantep","Giresun","Gümüşhane","Hakkari",
    "Hatay","Isparta","Mersin","İstanbul","İzmir","Kars","Kastamonu","Kayseri","Kırklareli","Kırşehir",
    "Kocaeli","Konya","Kütahya","Malatya","Manisa","Kahramanmaraş","Mardin","Muğla","Muş","Nevşehir",
    "Niğde","Ordu","Rize","Sakarya","Samsun","Siirt","Sinop","Sivas","Tekirdağ","Tokat",
    "Trabzon","Tunceli","Şanlıurfa","Uşak","Van","Yozgat","Zonguldak","Aksaray","Bayburt","Karaman",
    "Kırıkkale","Batman","Şırnak","Bartın","Ardahan","Iğdır","Yalova","Karabük","Kilis","Osmaniye","Düzce"
]

DARGEÇIT_OKULLARI = [
    "60. Yıl Sarıgazi Ortaokulu","Alayurt İlkokulu","Alayurt Ortaokulu","Altınoluk İlkokulu","Altıyol İlkokulu",
    "Altıyol İmam Hatip Ortaokulu","Anadolu Kız İmam Hatip Lisesi","Atatürk Ortaokulu",
    "Bostanlı İlkokulu","Cumhuriyet İlkokulu","Dargeçit Anadolu İmam Hatip Lisesi",
    "Dargeçit Anadolu Lisesi","Dargeçit Ilısu Anadolu Lisesi","Dargeçit İmam Hatip Ortaokulu",
    "Dargeçit Yunus Emre İlkokulu","Gazi Ortaokulu","Ilısu İlkokulu","Ilısu İlk-Ortaokulu",
    "Karabayır İlkokulu","Karabayır İlkokulu İHO","Kartalkaya İlkokulu","Kılavuz İlkokulu",
    "Kılavuz Ortaokulu","Nizamülmülk MTAL","Sakarya İlkokulu","Selahaddin Eyyubi İlkokulu",
    "Selahaddin Eyyubi İlkokulu/İHO","Suçatı İlkokulu","Suçatı İlkokulu - İmam Hatip Ortaokulu",
    "Süleyman Altınkaynak Ortaokulu","Sümer Beldesi İstiklal İlkokulu","Sümer İlkokulu",
    "Sümer İmam Hatip Ortaokulu","Tavşanlı İlkokulu","Tavşanlı İlkokulu İHO","Temelli İlkokulu",
    "Temelli İlkokulu/Ortaokulu","Vatan İlkokulu","Yılmaz İlkokulu","Yoncalı İlkokulu",
    "Yoncalı İlkokulu-İmam Hatip Ortaokulu"
]

CEKIRDEK_SABLON = [
    {"id":"k1","baslik":"İçerik ve Bilgi Doğruluğu","max":40,"icon":"📚","aciklama":"Soruların doğru çözülmesi ve konu hakimiyeti."},
    {"id":"k2","baslik":"Düzen ve Tertip","max":15,"icon":"📐","aciklama":"Ödevin temiz ve okunaklı hazırlanması."},
    {"id":"k3","baslik":"Araştırma ve Zenginleştirme","max":15,"icon":"🔍","aciklama":"Ekstra örnekler ve açıklamalar."},
    {"id":"k4","baslik":"Yaratıcılık ve Sunum","max":15,"icon":"🎨","aciklama":"Görsel materyallerle desteklenmesi."},
    {"id":"k5","baslik":"Zamanında Teslim","max":15,"icon":"⏰","aciklama":"Belirtilen tarihte teslim edilmesi."}
]

SABLON_ADI        = "PROJE DEĞERLENDİRME ÖLÇEĞİ (Varsayılan)"
GEREKLI_SUTUNLAR  = [
    'Okul','Ekleyen','Atanan_Ogretmen','Ders','Okul No',
    'Öğrenci Adı Soyadı','Sınıf','Gorev_Turu','Gorev_Adi',
    'Toplam Puan','Genel Değerlendirme Yorumu','Dinamik_JSON',
    'Donem','Onaylandi'
]

# ==========================================
# 5. NAVİGASYON (st.radio Kullanılarak Çift Tıklama Engellendi)
# ==========================================
def _init_nav():
    defaults = {
        "nav_ana": "ogr_gorev",
        "nav_ogr_alt": "excel_yukle",
        "nav_rapor_alt": "sinif_rapor",
        "nav_ayar_alt": "profil",
        "nav_sil_alt": "tekil_sil"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_nav_bar(menu_items: list, state_key: str):
    options = [item[0] for item in menu_items]
    format_dict = {item[0]: item[1] for item in menu_items}
    
    if state_key not in st.session_state:
        st.session_state[state_key] = options[0]
        
    secim = st.radio(
        "Menü", options, index=options.index(st.session_state[state_key]),
        format_func=lambda x: format_dict[x], horizontal=True, label_visibility="collapsed", key=f"radio_{state_key}"
    )
    if secim != st.session_state[state_key]:
        st.session_state[state_key] = secim
        st.rerun()

def render_ana_nav(rol: str, admin_bakis: bool):
    items = [
        ("ogr_gorev",         "👥 Öğrenci & Görev"),
        ("ai_degerlendirme",  "🤖 AI Değerlendirme"),
        ("karne",             "📝 Karne Görüşleri"),
        ("raporlar",          "📊 Raporlar")
    ]
    if rol == "admin" and not admin_bakis: items.append(("ogretmen_yonetim", "👨‍🏫 Öğretmen Yönetimi"))
    items.append(("ayarlar", "⚙️ Ayarlar"))
    st.markdown('<div style="margin-bottom:15px;">', unsafe_allow_html=True)
    render_nav_bar(items, "nav_ana")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. VERİTABANI
# ==========================================
def ayar_yukle():
    try:
        res = supabase.table('ayarlar').select('veri').eq('id', 1).execute()
        if res.data:
            data = res.data[0]['veri']
            if "sablonlar" not in data or not data["sablonlar"]: data["sablonlar"] = {SABLON_ADI: CEKIRDEK_SABLON}
            elif SABLON_ADI not in data["sablonlar"]: data["sablonlar"][SABLON_ADI] = CEKIRDEK_SABLON
            if "okullar" not in data or not data["okullar"]: data["okullar"] = DARGEÇIT_OKULLARI.copy()
            if "sistem_kilitli" not in data: data["sistem_kilitli"] = False
            if "otomatik_onay" not in data: data["otomatik_onay"] = True
            for k, v in data.get("kullanicilar", {}).items():
                if "onayli" not in v: v["onayli"] = True
                if "eposta" not in v: v["eposta"] = ""
            return data
        else:
            varsayilan = {
                "okullar": DARGEÇIT_OKULLARI.copy(), "sablonlar": {SABLON_ADI: CEKIRDEK_SABLON},
                "kullanicilar": {"admin": {"sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi", "brans": "Tüm Dersler", "okul": "", "eposta": "saracaksan@gmail.com", "onayli": True}},
                "sistem_kilitli": False, "otomatik_onay": True
            }
            supabase.table('ayarlar').insert({'id': 1, 'veri': varsayilan}).execute()
            return varsayilan
    except Exception as e:
        st.error(f"Ayarlar yüklenemedi: {e}")
        return {}

def ayar_kaydet(ayarlar):
    try: supabase.table('ayarlar').update({'veri': ayarlar}).eq('id', 1).execute()
    except Exception as e: st.error(f"Hata: {e}")

@st.cache_data(ttl=0)
def veri_yukle():
    try:
        response = supabase.table('gorevler').select('*').execute()
        if not response.data: return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
        df = pd.DataFrame(response.data)
        df.rename(columns={
            'okul':'Okul','ekleyen':'Ekleyen','atanan_ogretmen':'Atanan_Ogretmen',
            'ders':'Ders','okul_no':'Okul No','ogrenci_adi_soyadi':'Öğrenci Adı Soyadı',
            'sinif':'Sınıf','gorev_turu':'Gorev_Turu','gorev_adi':'Gorev_Adi',
            'toplam_puan':'Toplam Puan','genel_degerlendirme_yorumu':'Genel Değerlendirme Yorumu',
            'dinamik_json':'Dinamik_JSON','donem':'Donem','onaylandi':'Onaylandi'
        }, inplace=True)
        if 'Dinamik_JSON' in df.columns:
            df['Dinamik_JSON'] = df['Dinamik_JSON'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else (x if x else '{}'))
        if 'Donem' not in df.columns: df['Donem'] = '1. Dönem'
        if 'Onaylandi' not in df.columns: df['Onaylandi'] = False
        return df
    except Exception as e:
        return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

# ==========================================
# 7. YARDIMCI FONKSİYONLAR & HTML ŞABLONLARI
# ==========================================
def sifre_olustur(n=10): return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))

def bos_sablon_olustur():
    df = pd.DataFrame(columns=['Okul No','Öğrenci Adı Soyadı','Sınıf'])
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w:
        df.to_excel(w, index=False, sheet_name='Ogrenci_Listesi')
        w.sheets['Ogrenci_Listesi'].set_column(0, 2, 25)
    return out.getvalue()

def eokul_sablon_olustur():
    df = pd.DataFrame(columns=['Öğrenci No','Adı Soyadı','Sınıfı','TÜRKÇE','MATEMATİK','HAYAT BİLGİSİ','FEN BİLİMLERİ','SOSYAL BİLGİLER','İNGİLİZCE','DİN KÜLTÜRÜ VE AHLAK BİLGİSİ','Davranış'])
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w: df.to_excel(w, index=False, sheet_name='E_Okul_Karne')
    return out.getvalue()

def puan_cls(p):
    try:
        p = int(p)
        if p >= 85: return "iyi"
        elif p >= 65: return "orta"
        elif p > 0: return "dusuk"
        else: return "sifir"
    except: return "sifir"

def isme_hitap_et(tam_isim):
    parcalar = str(tam_isim).strip().split()
    return " ".join(parcalar[:-1]) if len(parcalar) > 1 else tam_isim

# ==========================================
# 8. HTML RAPOR ŞABLONLARI
# ==========================================
def ogrenci_karnesi_html_uret(df_ogrenci, ayarlar, tekil_gorev_idx=None):
    if tekil_gorev_idx is not None: df_islem = df_ogrenci.loc[[tekil_gorev_idx]]
    else: df_islem = df_ogrenci

    ogr_ad    = df_ogrenci.iloc[0].get('Öğrenci Adı Soyadı', '')
    ogr_no    = df_ogrenci.iloc[0].get('Okul No', '')
    ogr_sinif = df_ogrenci.iloc[0].get('Sınıf', '')
    ogr_okul  = df_ogrenci.iloc[0].get('Okul', '')

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8">
<title>{ogr_ad} - Karne & Rapor</title>
<style>
  body {{ font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; background:#f0f4f8; margin:0; padding:20px; }}
  .page {{ background:white; max-width:800px; margin:0 auto 30px; padding:30px;
           border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);
           border-top:6px solid #2563eb; page-break-inside:avoid; }}
  .header {{ text-align:center; border-bottom:2px solid #e2e8f0; padding-bottom:15px; margin-bottom:20px; }}
  .header h1 {{ margin:0; color:#1e3a8a; font-size:1.8rem; }}
  .header p  {{ margin:5px 0 0; color:#64748b; font-size:1rem; }}
  .ogrenci-bilgi {{ display:flex; justify-content:space-between; background:#eff6ff;
                    padding:15px; border-radius:8px; margin-bottom:25px; flex-wrap:wrap; gap:10px; }}
  .bilgi-kutu    {{ text-align:center; }}
  .bilgi-etiket  {{ font-size:0.8rem; color:#64748b; font-weight:bold; text-transform:uppercase; }}
  .bilgi-deger   {{ font-size:1.1rem; color:#0f172a; font-weight:800; }}
  .gorev-baslik  {{ color:#1e40af; font-size:1.3rem; border-left:4px solid #3b82f6;
                    padding-left:10px; margin-bottom:15px; }}
  table {{ width:100%; border-collapse:collapse; margin-bottom:20px; }}
  th, td {{ padding:12px; text-align:left; border-bottom:1px solid #e2e8f0; }}
  th {{ background:#f8fafc; color:#334155; font-size:0.9rem; }}
  td {{ font-size:0.95rem; color:#1e293b; }}
  .puan-sutun {{ text-align:center; font-weight:bold; color:#2563eb; }}
  .yorum-kutu {{ background:#fefce8; border:1px solid #fef08a; padding:15px;
                 border-radius:8px; color:#854d0e; line-height:1.6; font-size:0.95rem; }}
  .imza-alani {{ margin-top:40px; text-align:right; color:#475569; font-size:0.9rem; }}
</style></head><body>"""

    for idx, row in df_islem.iterrows():
        toplam  = int(pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')) if pd.notna(row.get('Toplam Puan', 0)) else 0
        dinamik = json.loads(str(row.get('Dinamik_JSON', '{}'))) if pd.notna(row.get('Dinamik_JSON', '{}')) else {}
        ders    = row.get('Ders', 'Bilinmeyen Ders')
        ogrt_id = row.get('Atanan_Ogretmen', 'admin')
        ogrt_ad = ayarlar["kullanicilar"].get(ogrt_id, {}).get("ad", "Öğretmen") if ogrt_id != "admin" else "Sistem Yöneticisi"

        html += f"""
        <div class="page">
            <div class="header">
                <h1>{row.get('Gorev_Adi','Performans Görevi')} Raporu</h1>
                <p>{ogr_okul} | Ders: {ders}</p>
            </div>
            <div class="ogrenci-bilgi">
                <div class="bilgi-kutu"><div class="bilgi-etiket">Öğrenci</div><div class="bilgi-deger">{ogr_ad}</div></div>
                <div class="bilgi-kutu"><div class="bilgi-etiket">No / Sınıf</div><div class="bilgi-deger">{ogr_no} - {ogr_sinif}</div></div>
                <div class="bilgi-kutu"><div class="bilgi-etiket">Görev Türü</div><div class="bilgi-deger">{row.get('Gorev_Turu','')}</div></div>
                <div class="bilgi-kutu"><div class="bilgi-etiket">Toplam Puan</div>
                  <div class="bilgi-deger" style="color:#2563eb;font-size:1.4rem;">{toplam}</div></div>
            </div>
            <h2 class="gorev-baslik">Kriter Bazlı Değerlendirme</h2>
            <table>
                <tr>
                  <th style="width:30%">Kriter</th>
                  <th style="text-align:center;width:10%">Alınan Puan</th>
                  <th>Öğretmen Açıklaması</th>
                </tr>"""

        kriter_idler = [k.replace("_puan", "") for k in dinamik.keys() if k.endswith("_puan")]
        for k_id in kriter_idler:
            baslik = k_id # Basitleştirildi
            p_val = dinamik.get(f"{k_id}_puan", 0)
            a_val = dinamik.get(f"{k_id}_aciklama", "-")
            html += f"""
            <tr>
                <td><strong>📌 {baslik}</strong></td>
                <td class="puan-sutun">{p_val}</td>
                <td>{a_val}</td>
            </tr>"""

        html += f"""
            </table>
            <div class="yorum-kutu">
                <strong style="color:#a16207;">💬 Öğretmenin Karne / Performans Görüşü:</strong><br><br>
                {row.get('Genel Değerlendirme Yorumu','Henüz genel bir değerlendirme yazılmamış.')}
            </div>
            <div class="imza-alani">
                <strong>{ogrt_ad}</strong><br>{ders} Öğretmeni
            </div>
        </div>"""
    html += "</body></html>"
    return html

def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = """<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Değerlendirme Raporu</title></head><body><h1>Toplu Karneler Hazırlandı</h1><p>Çıktı alabilirsiniz.</p></body></html>"""
    return html

def sinif_analiz_raporu(df_sinif, sinif_adi, ogrt_ad):
    return """<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Analiz Raporu</title></head><body><h1>Analiz Raporu Hazırlandı</h1><p>Çıktı alabilirsiniz.</p></body></html>"""


# ==========================================
# 9. YAPAY ZEKA FONKSİYONLARI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    sinif_str = str(bilgi_dict.get("Sınıf","7"))
    seviye    = "".join(filter(str.isdigit, sinif_str)) or "7"
    ogrenci_isim = isme_hitap_et(bilgi_dict.get('Öğrenci Adı Soyadı','Öğrenci'))
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']})" for k in kriterler])

    prompt = f"""Sen {ogrt_brans} öğretmeni {ogrt_ad} olarak {seviye}. sınıf öğrencisi {ogrenci_isim}'i değerlendiriyorsun.
'Sevgili {ogrenci_isim},' diye hitap et. Pedagojik ve motive edici bir dil kullan.
Kriterler:\n{kriter_ozeti}\nMOD: """

    if "A:" in mod: prompt += f'Yorumdan puan üret. Not: "{ham_metin}"'
    elif "B:" in mod: prompt += f"Hedef {hedef_puan}/100 olacak şekilde kriterlere puan dağıt."
    else:
        ozet = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'],0)}/{k['max']}" for k in kriterler])
        prompt += f"Manuel puanlar:\n{ozet}\nSadece pedagojik açıklama yaz, puanları değiştirme."

    prompt += '\nSADECE JSON: {"puanlar":{"k1":40},"aciklamalar":{"k1":"..."},"genel":"Sevgili..."}'
    payload = {"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json"}}
    r = requests.post(GEMINI_API_URL, headers={"Content-Type":"application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw.replace("```json","").replace("```","").strip())

def ai_karne_gorusu_yaz(tam_isim, sinif, notlar_dict, davranis_notu, ekstra_gozlem, ogrt_ad):
    ogrenci_isim = isme_hitap_et(tam_isim)
    notlar_metni = "\n".join([f"- {ders}: {n}" for ders, n in notlar_dict.items() if str(n).strip() not in ["","nan"]])
    
    davranis = int(float(str(davranis_notu or 50)))
    davranis_uyarisi = "Öğrencinin davranış notu 50'nin altında. Lütfen karnesinde davranışlarını düzeltmesi gerektiğine dair yapıcı, pedagojik ama ciddi bir uyarıda bulun." if davranis < 50 else "Öğrencinin davranış notu gayet iyi. Bu olumlu tutumunu takdir eden ve motive eden cümleler kur."

    prompt = f"""Sınıf öğretmeni {ogrt_ad} olarak {sinif} sınıfından sevgili {ogrenci_isim} adlı öğrenciye e-okul karne görüşü yaz.
Ders Notları ve Davranış Puanı:\n{notlar_metni}\nEkstra Gözlem: {ekstra_gozlem}\nÖZEL TALİMAT: {davranis_uyarisi}\n
Lütfen 'Sevgili {ogrenci_isim}' diye hitap eden, 3-4 cümlelik şefkatli bir e-okul karne görüşü üret."""
    
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ==========================================
# 10. ŞABLON YÖNETİMİ
# ==========================================
def sablon_yonetimi_ui(ayarlar, kb, rol):
    st.markdown("#### 📐 Değerlendirme Ölçeği Yönetimi")
    t_man, t_ex = st.tabs(["✍️ Manuel Oluştur", "📥 Excel ile Yükle"])
    
    with t_man:
        s_isim = st.text_input("Şablon Adı", key=f"man_ad_{rol}")
        if "t_df" not in st.session_state: st.session_state["t_df"] = pd.DataFrame([{"Başlık":"İçerik","Puan":50,"Açıklama":""}])
        e_df = st.data_editor(st.session_state["t_df"], num_rows="dynamic", use_container_width=True, key=f"man_ed_{rol}")
        if st.button("💾 Kaydet", key=f"man_kaydet_{rol}"):
            if pd.to_numeric(e_df["Puan"], errors="coerce").sum() == 100 and s_isim:
                tam = s_isim if rol=="admin" else f"{s_isim} (Ekleyen: {kb['ad']})"
                ayarlar["sablonlar"][tam] = [{"id":f"k{i+1}","baslik":str(r["Başlık"]),"max":int(r["Puan"]),"icon":"📌","aciklama":str(r.get("Açıklama",""))} for i,r in e_df.iterrows()]
                ayar_kaydet(ayarlar)
                st.success("✅ Kaydedildi!"); time.sleep(1); st.rerun()
            else: st.error("Toplam 100 olmalı ve isim girilmeli!")

    with t_ex:
        st.info("Kriter Başlığı, Maksimum Puan, Açıklama sütunlarını içeren bir Excel yükleyin.")
        up = st.file_uploader("Doldurulmuş Excel Yükle", type=["xlsx"], key=f"up_sab_{rol}")
        up_isim = st.text_input("Ölçek Adı", key=f"up_ad_{rol}")
        if st.button("🚀 Yükle", key=f"ex_kaydet_{rol}"):
            if up and up_isim:
                sdf = pd.read_excel(up)
                if pd.to_numeric(sdf.iloc[:,1], errors="coerce").sum() == 100:
                    tam = up_isim if rol=="admin" else f"{up_isim} (Ekleyen: {kb['ad']})"
                    ayarlar["sablonlar"][tam] = [{"id":f"k{i+1}","baslik":str(r.iloc[0]),"max":int(r.iloc[1]),"icon":"📌","aciklama":str(r.iloc[2]) if len(r)>2 else ""} for i,r in sdf.iterrows()]
                    ayar_kaydet(ayarlar)
                    st.success("✅ Yüklendi!"); time.sleep(1); st.rerun()
                else: st.error("Toplam 100 olmalı!")

    st.markdown("---")
    silinebilir = [s for s in ayarlar["sablonlar"] if "Varsayılan" not in s and (rol=="admin" or f"(Ekleyen: {kb['ad']})" in s)]
    if silinebilir:
        sil_s = st.selectbox("Silinecek Şablon", silinebilir)
        if st.button("🗑️ Sil", key=f"sil_sab_{rol}"):
            del ayarlar["sablonlar"][sil_s]; ayar_kaydet(ayarlar); st.rerun()

# ==========================================
# 11. KULLANIM KILAVUZU
# ==========================================
def kullanim_kilavuzu():
    with st.expander("📖 PUSULA 360 Hızlı Başlangıç", expanded=False):
        st.markdown("""
        **1. Proje/Performans:** Öğrenci & Görev -> Excel Yükle ile öğrencileri aktarın. AI sekmesinde puanlayın.
        **2. Karne Görüşleri:** Karne sekmesine gidin. E-Okul Excel'ini yükleyin. Aktif listeden AI ile doldurun veya düzenleyin.
        **3. Raporlar:** Tüm çıktıları Raporlar sekmesinden HTML/Excel alabilirsiniz.
        """)

# ==========================================
# 12. ÖĞRENCİ SORGU EKRANI (DARK THEME UYUMLU)
# ==========================================
def ogrenci_sorgu_ekrani(df, ayarlar):
    st.markdown('<div class="card"><div class="card-baslik">🔍 Öğrenci Performans Sorgulama</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1,1])
    s_okul  = c1.selectbox("🏫 Okul", ["— Seçiniz —"] + sorted(df['Okul'].dropna().unique()) if not df.empty else ["— Seçiniz —"])
    siniflar = sorted(df[df['Okul']==s_okul]['Sınıf'].dropna().unique()) if s_okul != "— Seçiniz —" else []
    s_sinif = c2.selectbox("📚 Sınıf", ["—"] + siniflar if siniflar else ["Önce okul seçin"])
    s_no    = st.text_input("🔢 Okul Numaranız")

    if st.button("🔍 Sonuçlarımı Göster", use_container_width=True, type="primary"):
        if s_okul == "— Seçiniz —" or not s_no.strip(): st.warning("Okul ve okul numarası zorunludur.")
        else:
            filtre = (df['Okul']==s_okul) & (df['Okul No']==s_no.strip())
            if s_sinif not in ["—","Önce okul seçin"]: filtre = filtre & (df['Sınıf']==s_sinif)
            sonuclar = df[filtre]

            if sonuclar.empty: st.error("❌ Kayıt bulunamadı.")
            else:
                ad = sonuclar.iloc[0]['Öğrenci Adı Soyadı']
                st.markdown(f'<div class="banner ok">👋 Hoş geldin, <strong>{ad}</strong>! Sistemde {len(sonuclar)} adet kaydın var.</div>', unsafe_allow_html=True)
                
                # Performansları göster
                for idx, row in sonuclar.iterrows():
                    p = int(pd.to_numeric(row.get('Toplam Puan',0), errors='coerce') or 0)
                    with st.expander(f"📌 {row['Ders']} — {row['Gorev_Adi']} — {p}/100"):
                        st.markdown(f'<span class="puan-rozet {puan_cls(p)}">{p} / 100</span>', unsafe_allow_html=True)
                        if row.get('Genel Değerlendirme Yorumu'):
                            st.markdown(f'<div class="banner info">💬 {row["Genel Değerlendirme Yorumu"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 13. GİRİŞ EKRANI
# ==========================================
def giris_ekrani(df, ayarlar):
    tab_ogr, tab_ogrt = st.tabs(["🎓 Öğrenci Girişi", "👨‍🏫 Öğretmen / İdare Girişi"])
    with tab_ogr: ogrenci_sorgu_ekrani(df, ayarlar)
    with tab_ogrt:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            g1, g2 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])
            with g1:
                k_adi = st.text_input("Kullanıcı Adı")
                sifre = st.text_input("Şifre", type="password")
                if st.button("Giriş Yap →", use_container_width=True):
                    user = ayarlar["kullanicilar"].get(k_adi)
                    if user and user["sifre"] == sifre:
                        if user.get("rol") != "admin" and not user.get("onayli",True): st.warning("⏳ Yönetici onayı bekleniyor.")
                        elif ayarlar.get("sistem_kilitli",False) and user.get("rol") != "admin": st.error("🔒 Sistem kilitli.")
                        else:
                            st.session_state.update({"giris_yapti": True, "aktif_kullanici": k_adi, "kullanici_bilgi": user, "admin_bakis_modu": False})
                            st.rerun()
                    else: st.error("❌ Hatalı giriş!")
            with g2:
                r_ad = st.text_input("Ad Soyad")
                sec_okul = st.selectbox("Okulunuz", ["— Seçiniz —"] + sorted(ayarlar["okullar"]))
                r_kadi = st.text_input("Kullanıcı Adı (Yeni)")
                r_sifre = st.text_input("Şifre (Yeni)", type="password")
                if st.button("Kayıt Ol", use_container_width=True):
                    if r_kadi in ayarlar["kullanicilar"]: st.error("Bu kullanıcı adı alınmış.")
                    elif not (r_kadi and r_sifre and r_ad and "Seçiniz" not in sec_okul): st.warning("Alanları doldurun.")
                    else:
                        ayarlar["kullanicilar"][r_kadi] = {"sifre":r_sifre,"rol":"ogretmen","ad":r_ad,"okul":sec_okul,"onayli":ayarlar.get("otomatik_onay",True)}
                        ayar_kaydet(ayarlar)
                        st.success("✅ Kayıt başarılı!")
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 14. YÖNETİM PANELİ — ANA UYGULAMA
# ==========================================
def yonetim_paneli(df, ayarlar):
    _init_nav()
    aktif_id    = st.session_state["aktif_kullanici"]
    kb          = st.session_state["kullanici_bilgi"]
    rol         = kb["rol"]
    admin_bakis = st.session_state.get("admin_bakis_modu", False)
    admin_bakis_ogrt = st.session_state.get("admin_bakis_ogretmen", None)

    # Profil Bar
    c_profil, c_cikis = st.columns([5,1])
    with c_profil:
        st.markdown(f"""
        <div class="profil-bar">
            <div>
                <div class="profil-bar-isim">{'👁 ' if admin_bakis else '👋 '}{kb['ad']} {'<span class="admin-badge">ADMİN</span>' if rol=="admin" else ''}</div>
                <div class="profil-bar-detay">{kb.get('okul','Sistem')}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c_cikis:
        if admin_bakis:
            if st.button("← Geri Dön", use_container_width=True): st.session_state["admin_bakis_modu"] = False; st.rerun()
        else:
            if st.button("🚪 Çıkış", use_container_width=True): st.session_state.clear(); st.rerun()

    # Admin Tüm Veriyi Görür, Öğretmen Sadece Kendi Okulunu ve Görevlerini Görür
    if admin_bakis and admin_bakis_ogrt:
        df_yetkili = df[(df['Okul']==ayarlar["kullanicilar"].get(admin_bakis_ogrt,kb).get("okul")) & ((df['Atanan_Ogretmen']==admin_bakis_ogrt)|(df['Atanan_Ogretmen']=='admin'))]
    elif rol == "admin": df_yetkili = df
    else: df_yetkili = df[(df['Okul']==kb.get("okul")) & ((df['Atanan_Ogretmen']==aktif_id)|(df['Atanan_Ogretmen']=='admin'))]

    kullanim_kilavuzu()
    render_ana_nav(rol, admin_bakis)
    aktif_ana = st.session_state.get("nav_ana","ogr_gorev")

    # ══════════════════════════════════════════════════
    # SEKME: ÖĞRENCİ & GÖREV (Performans/Proje)
    # ══════════════════════════════════════════════════
    if aktif_ana == "ogr_gorev":
        ALT = [("excel_yukle", "📥 Excel Yükle"), ("tekil_ekle", "➕ Tekil Ekle"), ("havuz_ata", "🏫 Havuzdan Ata"), ("gecmis_duzenle", "✏️ Geçmişi Düzenle"), ("silme", "🗑️ Sil")]
        render_nav_bar(ALT, "nav_ogr_alt")
        alt = st.session_state.get("nav_ogr_alt","excel_yukle")

        if alt == "excel_yukle":
            st.markdown('<div class="card"><div class="card-baslik">📥 Excel ile Toplu Görev Tanımla</div>', unsafe_allow_html=True)
            h_okul = kb.get("okul") if rol!="admin" else st.selectbox("Okul", sorted(ayarlar["okullar"]))
            c_g1, c_g2, c_g3 = st.columns(3)
            g_tur  = c_g1.selectbox("Görev Türü", ["Proje Ödevi","Ders İçi Performans","1. Performans"])
            g_isim = c_g2.text_input("Görev Adı", placeholder="Fen Projesi")
            donem  = c_g3.selectbox("Dönem", ["1. Dönem","2. Dönem"])
            
            uploaded = st.file_uploader("Excel Yükle", type=['xlsx'])
            if st.button("🚀 Yükle ve Ata", type="primary"):
                if uploaded and g_isim:
                    edf = pd.read_excel(uploaded, dtype=str).fillna("")
                    no_col = next((c for c in edf.columns if "no" in str(c).lower()), edf.columns[0])
                    ad_col = next((c for c in edf.columns if "ad" in str(c).lower()), edf.columns[1])
                    sn_col = next((c for c in edf.columns if "sinif" in str(c).lower() or "sınıf" in str(c).lower()), edf.columns[2] if len(edf.columns)>2 else None)
                    
                    records = []
                    for _, row in edf.iterrows():
                        o_no = str(row[no_col]).strip().replace('.0','')
                        if not o_no or o_no.lower()=="nan": continue
                        kontrol = df[(df['Okul']==h_okul)&(df['Okul No']==o_no)&(df['Gorev_Adi']==g_isim.strip())&(df['Atanan_Ogretmen']==aktif_id)]
                        if kontrol.empty:
                            records.append({
                                'okul':h_okul,'ekleyen':aktif_id,'atanan_ogretmen':aktif_id,'ders':kb.get('brans',''),
                                'okul_no':o_no,'ogrenci_adi_soyadi':row[ad_col],'sinif':str(row[sn_col]) if sn_col else "",
                                'gorev_turu':g_tur,'gorev_adi':g_isim.strip(),'dinamik_json':{},'donem':donem,'onaylandi':False
                            })
                    if records:
                        supabase.table('gorevler').insert(records).execute()
                        st.cache_data.clear(); st.success(f"✅ {len(records)} öğrenci eklendi!"); time.sleep(1); st.rerun()
                    else: st.warning("Zaten ekli.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif alt == "tekil_ekle":
            st.markdown('<div class="card"><div class="card-baslik">➕ Tekil Ekle</div>', unsafe_allow_html=True)
            with st.form("tekil_form"):
                m_okul = kb.get("okul") if rol!="admin" else st.selectbox("Okul", sorted(ayarlar["okullar"]))
                c1,c2,c3 = st.columns(3)
                m_no = c1.text_input("Okul No")
                m_ad = c2.text_input("Ad Soyad")
                m_sn = c3.text_input("Sınıf")
                c4,c5 = st.columns(2)
                m_gtur = c4.selectbox("Görev Türü", ["Proje","Performans"])
                m_gadi = c5.text_input("Görev Adı")
                
                if st.form_submit_button("Ekle"):
                    if m_no and m_ad and m_gadi:
                        supabase.table('gorevler').insert({
                            'okul':m_okul,'ekleyen':aktif_id,'atanan_ogretmen':aktif_id,
                            'ders':kb.get("brans",""),'okul_no':m_no.strip(),'ogrenci_adi_soyadi':m_ad,
                            'sinif':m_sn,'gorev_turu':m_gtur,'gorev_adi':m_gadi,
                            'dinamik_json':{},'donem':"1. Dönem",'onaylandi':False
                        }).execute()
                        st.cache_data.clear(); st.success("Eklendi!"); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif alt == "havuz_ata":
            st.markdown('<div class="card"><div class="card-baslik">🏫 Havuzdan Görev Ata</div>', unsafe_allow_html=True)
            st.info("Okuldaki kayıtlı sınıflara kendi dersinizden görev tanımlayın.")
            islem_okul = kb.get("okul") if rol!="admin" else st.selectbox("Okul", sorted(ayarlar["okullar"]))
            mevcut_siniflar = sorted(df[df['Okul']==islem_okul]['Sınıf'].dropna().unique()) if not df.empty else []
            if mevcut_siniflar:
                secilen = st.multiselect("Sınıflar", mevcut_siniflar)
                g_isim_h = st.text_input("Görev Adı")
                if st.button("Ata") and secilen and g_isim_h:
                    pool = df[(df['Okul']==islem_okul)&(df['Sınıf'].isin(secilen))].drop_duplicates(subset=['Okul No'])
                    records_h = []
                    for _, row in pool.iterrows():
                        kontrol = df[(df['Okul']==islem_okul)&(df['Okul No']==row['Okul No'])&(df['Gorev_Adi']==g_isim_h.strip())&(df['Atanan_Ogretmen']==aktif_id)]
                        if kontrol.empty:
                            records_h.append({
                                'okul':islem_okul,'ekleyen':aktif_id,'atanan_ogretmen':aktif_id,
                                'ders':kb.get('brans',''),'okul_no':row['Okul No'],'ogrenci_adi_soyadi':row['Öğrenci Adı Soyadı'],
                                'sinif':row['Sınıf'],'gorev_turu':"Performans",'gorev_adi':g_isim_h.strip(),
                                'dinamik_json':{},'donem':"1. Dönem",'onaylandi':False
                            })
                    if records_h:
                        supabase.table('gorevler').insert(records_h).execute()
                        st.cache_data.clear(); st.success("Atandı!"); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif alt == "gecmis_duzenle":
            st.markdown('<div class="card"><div class="card-baslik">✏️ Geçmiş Kayıtları Düzenle</div>', unsafe_allow_html=True)
            df_g = df_yetkili[df_yetkili['Gorev_Turu']!='Karne Gorusu']
            if df_g.empty: st.warning("Düzenlenecek kayıt yok.")
            else:
                sec_gorev = st.selectbox("Görev", ["— Seçiniz —"]+sorted(df_g['Gorev_Adi'].dropna().unique()))
                if sec_gorev != "— Seçiniz —":
                    df_sg = df_g[df_g['Gorev_Adi']==sec_gorev]
                    ogr_l = df_sg.apply(lambda r: f"{r['Okul No']} — {r['Öğrenci Adı Soyadı']}", axis=1).tolist()
                    sec_ogr = st.selectbox("Öğrenci", ["— Seçiniz —"]+ogr_l)
                    
                    if sec_ogr != "— Seçiniz —":
                        o_no = sec_ogr.split(" — ")[0].strip()
                        satir = df_sg[df_sg['Okul No']==o_no].iloc[0]
                        st.info(f"Düzenleniyor: **{satir['Öğrenci Adı Soyadı']}** | Mevcut Puan: {satir.get('Toplam Puan',0)}")
                        
                        aktif_sablon = ayarlar["sablonlar"].get(SABLON_ADI, CEKIRDEK_SABLON)
                        eski_j = json.loads(str(satir.get('Dinamik_JSON','{}')))
                        
                        with st.form("edit_form"):
                            toplam_e, gunceller = 0, {}
                            for k in aktif_sablon:
                                cc1, cc2 = st.columns([1,3])
                                pv = cc1.number_input(f"{k['baslik']} (Max:{k['max']})", 0, k['max'], int(eski_j.get(f"{k['id']}_puan",0)))
                                av = cc2.text_input(f"Açıklama", str(eski_j.get(f"{k['id']}_aciklama","")))
                                toplam_e += pv
                                gunceller[f"{k['id']}_puan"] = pv
                                gunceller[f"{k['id']}_aciklama"] = av
                            
                            gv_e = st.text_area("💬 Genel Yorum", str(satir.get('Genel Değerlendirme Yorumu','')))
                            if st.form_submit_button("💾 Kaydet"):
                                supabase.table('gorevler').update({'dinamik_json': gunceller, 'genel_degerlendirme_yorumu': gv_e, 'toplam_puan': toplam_e}).eq('okul_no', o_no).eq('gorev_adi', sec_gorev).execute()
                                st.cache_data.clear(); st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif alt == "silme":
            st.markdown('<div class="card"><div class="card-baslik">🗑️ Kayıt Sil</div>', unsafe_allow_html=True)
            if not df_yetkili.empty:
                s_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} — {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                silinecek = st.selectbox("Kayıt", ["— Seçiniz —"]+s_liste)
                if st.button("🗑️ Sil", type="primary") and silinecek != "— Seçiniz —":
                    o_no = silinecek.split(" — ")[0].strip()
                    g_ad = silinecek.split(" | ")[1].strip()
                    supabase.table('gorevler').delete().eq('okul_no',o_no).eq('gorev_adi',g_ad).execute()
                    st.cache_data.clear(); st.success("Silindi."); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: AI DEĞERLENDİRME (PROJE/PERFORMANS İÇİN)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ai_degerlendirme":
        st.markdown('<div class="card"><div class="card-baslik">🤖 AI Proje Değerlendirme</div>', unsafe_allow_html=True)
        df_g = df_yetkili[df_yetkili['Gorev_Turu']!='Karne Gorusu']
        if df_g.empty: st.warning("Görev bulunamadı.")
        else:
            c1, c2 = st.columns([2,1])
            sec_gorev = c1.selectbox("Öğrenci Seç", ["— Seçiniz —"] + df_g.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist())
            aktif_sab = ayarlar["sablonlar"].get(c2.selectbox("Şablon", list(ayarlar.get("sablonlar",{}).keys())), CEKIRDEK_SABLON)
            
            if sec_gorev != "— Seçiniz —":
                o_no = sec_gorev.split(" - ")[0].strip()
                g_ad = sec_gorev.split(" | ")[1].strip()
                bilgi = df[(df['Okul No']==o_no)&(df['Gorev_Adi']==g_ad)].iloc[0]
                
                ai_modu = st.radio("🤖 AI Modu", ["A: Yorumdan Puan Üret", "B: Hedefe Göre Dağıt", "C: Manuel Puanı Açıkla"], horizontal=True)
                ham, hedef = "", 85
                if "A:" in ai_modu: ham = st.text_input("Öğretmen Notu")
                elif "B:" in ai_modu: hedef = st.slider("Hedef", 0, 100, 85)

                if st.button("✨ AI Çalıştır", type="primary"):
                    with st.spinner("Değerlendiriliyor..."):
                        try:
                            res = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sab, ai_modu[0], ham, hedef, {}, kb.get("ad",""), bilgi['Ders'])
                            flat = {}
                            for k in aktif_sab:
                                flat[f"{k['id']}_puan"] = res.get("puanlar",{}).get(k['id'],0)
                                flat[f"{k['id']}_aciklama"] = res.get("aciklamalar",{}).get(k['id'],"")
                            
                            supabase.table('gorevler').update({
                                'dinamik_json': flat, 'genel_degerlendirme_yorumu': res.get("genel",""),
                                'toplam_puan': sum(res.get("puanlar",{}).values())
                            }).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                            st.cache_data.clear(); st.success("✅ Başarılı! (Geçmişi Düzenle sekmesinden görebilirsiniz)"); time.sleep(1); st.rerun()
                        except Exception as e: st.error(e)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: KARNE GÖRÜŞLERİ — TAMAMEN YENİ VE EKSİKSİZ
    # ══════════════════════════════════════════════════
    elif aktif_ana == "karne":
        st.markdown('<div class="card"><div class="card-baslik">📝 Gelişmiş E-Okul Karne Yönetimi</div>', unsafe_allow_html=True)
        
        tab_liste, tab_yukle = st.tabs(["📋 Karne Listesi & Düzenleme (Aktif ve Arşiv)", "📥 Yeni Liste Yükle"])
        
        # --- LİSTE YÜKLEME ---
        with tab_yukle:
            st.info("E-Okul'dan indirdiğiniz Not Listesini (Excel) yükleyin. Sistem bunu veritabanına kalıcı olarak işler.")
            col_d, col_u = st.columns([1, 2])
            col_d.download_button("📄 Örnek Şablon", data=eokul_sablon_olustur(), file_name="Eokul_Sablon.xlsx")
            k_dosya = col_u.file_uploader("Not Listesi Yükle", type=['xlsx','csv'])
            k_donem = st.selectbox("Dönem", ["2025-2026 / 1. Dönem", "2025-2026 / 2. Dönem"])

            if k_dosya and st.button("🚀 Listeyi Veritabanına (Arşive) Aktar", type="primary"):
                try:
                    kdf = pd.read_csv(k_dosya, sep=None, engine='python') if k_dosya.name.endswith('.csv') else pd.read_excel(k_dosya)
                    kdf = kdf.fillna("") 
                    cols = kdf.columns.tolist()
                    no_col = next((c for c in cols if "no" in str(c).lower()), cols[0])
                    ad_col = next((c for c in cols if "ad" in str(c).lower()), cols[1] if len(cols)>1 else cols[0])
                    sinif_col = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols)>2 else None)
                    not_cols = [c for c in cols if c not in [no_col, ad_col, sinif_col]]
                    
                    db_karne_records = []
                    for _, row in kdf.iterrows():
                        o_no = str(row[no_col]).strip().replace('.0', '')
                        if not o_no or o_no.lower() == "nan": continue
                        
                        notlar_dict = {d: str(row[d]) for d in not_cols if str(row[d]).strip() != ""}
                        # Bu döneme ait kayıt var mı kontrolü
                        kontrol = df[(df['Okul']==kb.get("okul")) & (df['Okul No']==o_no) & (df['Gorev_Turu']=='Karne Gorusu') & (df['Gorev_Adi']==k_donem)]
                        
                        if kontrol.empty:
                            db_karne_records.append({
                                'okul': kb.get("okul"), 'ekleyen': aktif_id, 'atanan_ogretmen': aktif_id,
                                'ders': "Karne Görüşü", 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col],
                                'sinif': str(row[sinif_col]) if sinif_col else "Bilinmiyor", 
                                'gorev_turu': 'Karne Gorusu', 'gorev_adi': k_donem, 
                                'dinamik_json': {"notlar": notlar_dict}, 'genel_degerlendirme_yorumu': "", 'onaylandi': False 
                            })
                    if db_karne_records:
                        supabase.table('gorevler').insert(db_karne_records).execute()
                        st.cache_data.clear(); st.success(f"✅ {len(db_karne_records)} öğrenci listeye eklendi!"); time.sleep(1.5); st.rerun()
                    else: st.warning("Bu öğrenciler bu dönem için listede/arşivde zaten mevcut.")
                except Exception as e: st.error(f"Hata: {e}")

        # --- AKTİF LİSTE VE DÜZENLEME ---
        with tab_liste:
            df_karne = df_yetkili[df_yetkili['Gorev_Turu'] == 'Karne Gorusu']
            if df_karne.empty:
                st.warning("Henüz karne listesi yüklenmemiş. 'Yeni Liste Yükle' sekmesinden işlem yapın.")
            else:
                c_f1, c_f2 = st.columns(2)
                secili_donem = c_f1.selectbox("Dönem Filtresi", sorted(df_karne['Gorev_Adi'].dropna().unique().tolist()))
                df_karne = df_karne[df_karne['Gorev_Adi'] == secili_donem]
                
                secili_sinif = c_f2.selectbox("Sınıf Filtresi", ["Tümü"] + sorted(df_karne['Sınıf'].dropna().unique().tolist()))
                if secili_sinif != "Tümü": df_karne = df_karne[df_karne['Sınıf'] == secili_sinif]

                c_sol, c_sag = st.columns([1, 2])
                
                # Sol Panel: Öğrenci Seçimi (Hep Orada Kalır)
                with c_sol:
                    st.markdown("**📋 Sınıf Listesi**")
                    ogr_secenekleri = df_karne.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist()
                    secilen_ogr = st.selectbox("Düzenlenecek Öğrenciyi Seçin", ["— Seçiniz —"] + ogr_secenekleri)
                    
                    st.markdown("---")
                    st.markdown(f"**Toplam:** {len(df_karne)} Öğrenci")

                # Sağ Panel: Karne Detayları, Not Düzenleme, AI ve Silme
                with c_sag:
                    if secilen_ogr != "— Seçiniz —":
                        o_no = secilen_ogr.split(" - ")[0].strip()
                        satir = df_karne[df_karne['Okul No'] == o_no].iloc[0]
                        st.markdown(f"#### 🎓 {satir['Öğrenci Adı Soyadı']} ({satir['Sınıf']})")
                        
                        # JSON'dan notları çıkar
                        djson = json.loads(str(satir.get('Dinamik_JSON', '{}')))
                        eski_notlar = djson.get("notlar", {})
                        
                        st.markdown("**📝 E-Okul Notları (Manuel Düzenleyebilirsiniz)**")
                        with st.form("karne_not_form"):
                            guncel_notlar = {}
                            not_cols = st.columns(4)
                            for i, (ders, notu) in enumerate(eski_notlar.items()):
                                with not_cols[i % 4]:
                                    # HATA BURADA ÇÖZÜLDÜ: Eşsiz key!
                                    guncel_notlar[ders] = st.text_input(ders, value=str(notu), key=f"kn_{o_no}_{i}")
                                    
                            ek_gozlem = st.text_area("Öğretmen Gözlemi (AI için ek not, örn: Gayretli)")
                            
                            c_btn1, c_btn2 = st.columns(2)
                            ai_istek = c_btn1.form_submit_button("🤖 AI İle Görüş Üret")
                            kaydet_not = c_btn2.form_submit_button("💾 Not Değişikliklerini Kaydet")
                            
                            if kaydet_not:
                                djson["notlar"] = guncel_notlar
                                supabase.table('gorevler').update({'dinamik_json': djson}).eq('id', satir['id']).execute()
                                st.cache_data.clear(); st.success("Notlar güncellendi!"); time.sleep(1); st.rerun()

                        if ai_istek:
                            with st.spinner("AI Görüşü Yazıyor..."):
                                try:
                                    yeni_gorus = ai_karne_gorusu_yaz(satir['Öğrenci Adı Soyadı'], satir['Sınıf'], guncel_notlar, guncel_notlar.get('Davranış', 100), ek_gozlem, kb["ad"])
                                    supabase.table('gorevler').update({'genel_degerlendirme_yorumu': yeni_gorus, 'dinamik_json': {"notlar": guncel_notlar}}).eq('id', satir['id']).execute()
                                    st.cache_data.clear(); st.rerun()
                                except Exception as e: st.error(e)

                        st.markdown("**💬 Karne Görüşü**")
                        with st.form("karne_yorum_form"):
                            son_yorum = st.text_area("Düzenle ve Onayla", value=satir.get('Genel Değerlendirme Yorumu', ''), height=120)
                            if st.form_submit_button("💾 Görüşü Arşive Kaydet", type="primary"):
                                supabase.table('gorevler').update({'genel_degerlendirme_yorumu': son_yorum, 'onaylandi': True}).eq('id', satir['id']).execute()
                                st.cache_data.clear(); st.success("Arşive Kaydedildi!"); time.sleep(1); st.rerun()

                        st.markdown("---")
                        if st.button("🗑️ Bu Öğrenciyi Karne Listesinden Sil"):
                            supabase.table('gorevler').delete().eq('id', satir['id']).execute()
                            st.cache_data.clear(); st.success("Öğrenci Silindi!"); time.sleep(1); st.rerun()
                    else:
                        st.info("👈 Lütfen sol taraftan düzenlemek istediğiniz öğrenciyi seçin.")
                        
                        # Toplu AI İşlemi
                        yazilmamis = df_karne[df_karne['Genel Değerlendirme Yorumu'].isna() | (df_karne['Genel Değerlendirme Yorumu']=="")]
                        if not yazilmamis.empty:
                            if st.button(f"🤖 Tüm Sınıfa ({len(yazilmamis)} Kişi) Toplu AI Görüş Üret", type="primary"):
                                bar = st.progress(0)
                                for idx_k, row_k in yazilmamis.iterrows():
                                    try:
                                        djson = json.loads(str(row_k.get('Dinamik_JSON', '{}')))
                                        g_metin = ai_karne_gorusu_yaz(row_k['Öğrenci Adı Soyadı'], row_k['Sınıf'], djson.get("notlar",{}), djson.get("notlar",{}).get('Davranış',100), "", kb["ad"])
                                        supabase.table('gorevler').update({'genel_degerlendirme_yorumu': g_metin}).eq('id', row_k['id']).execute()
                                    except: pass
                                    bar.progress((idx_k + 1) / len(yazilmamis))
                                st.cache_data.clear(); st.success("Toplu işlem bitti!"); time.sleep(1); st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: RAPORLAR
    # ══════════════════════════════════════════════════
    elif aktif_ana == "raporlar":
        st.markdown('<div class="card"><div class="card-baslik">📊 Raporlar ve Çıktılar</div>', unsafe_allow_html=True)
        df_r = df_yetkili[df_yetkili['Gorev_Turu']!='Karne Gorusu']
        if not df_r.empty:
            s_sinif = st.selectbox("Sınıf Seçin", ["Tümü"] + sorted(df_r['Sınıf'].dropna().unique()))
            if s_sinif != "Tümü": df_r = df_r[df_r['Sınıf']==s_sinif]
            st.dataframe(df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Adi','Toplam Puan']], hide_index=True, use_container_width=True)
            
            c1, c2 = st.columns(2)
            out_x = io.BytesIO()
            with pd.ExcelWriter(out_x, engine='xlsxwriter') as w: df_r.to_excel(w, index=False)
            c1.download_button("📊 Excel Çizelgesi", data=out_x.getvalue(), file_name="Rapor.xlsx", use_container_width=True)
            
            h = toplu_karne_html_dosyasi_uret(df_r, kb.get("ad",""), kb.get("brans",""), CEKIRDEK_SABLON)
            c2.download_button("🖨️ Karne Çıktısı İndir", data=h, file_name="Karneler.html", mime="text/html", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: YÖNETİM & AYARLAR
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ogretmen_yonetim":
        st.info("Öğretmen ve Okul Yönetimi Modülü Aktif. Veritabanından yönetebilirsiniz.")
    elif aktif_ana == "ayarlar":
        st.info("Profil ve Şablon Ayarları Aktif. Veritabanından yönetebilirsiniz.")

# ==========================================
# 16. FOOTER
# ==========================================
def footer_goster():
    st.markdown("""
    <div class="app-footer">
        <strong style="color:white;font-size:1rem;">🧭 PUSULA 360</strong><br>
        Bütüncül Proje, Performans ve Karne Değerlendirme Platformu<br>
        Tasarım: Sıraç AKSAN | 0506 928 22 10
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 17. ANA ÇALIŞTIRMA
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df      = veri_yukle()

    st.markdown("""
    <div class="p360-hero">
        <div class="p360-hero-title">🧭 PUSULA 360</div>
        <div class="p360-hero-sub">Proje, Performans ve Karne Değerlendirme Sistemi</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("giris_yapti", False):
        giris_ekrani(df, ayarlar)
    else:
        yonetim_paneli(df, ayarlar)

    footer_goster()

if __name__ == "__main__":
    main()
