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
# 3. GLOBAL CSS — MOBİL UYUMLU, PROFESYONEL
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Lexend:wght@400;600;800&display=swap');

/* ── Reset & Temel ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #f8fafc;
    color: #0f172a;
}
.block-container {
    padding: 0.5rem 1rem 2rem !important;
    max-width: 1280px !important;
}

/* ── Hero ── */
.p360-hero {
    background: linear-gradient(135deg, #0c1e4a 0%, #1a3a8f 50%, #2563eb 100%);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(30,58,138,0.3);
}
.p360-hero::after {
    content: '';
    position: absolute;
    top: -60%;
    right: -10%;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(255,255,255,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.p360-hero-title {
    font-family: 'Lexend', sans-serif;
    font-size: clamp(1.3rem, 4vw, 2rem);
    font-weight: 800;
    color: #fff;
    margin: 0;
    letter-spacing: -0.3px;
}
.p360-hero-sub {
    color: #93c5fd;
    font-size: clamp(0.78rem, 2.5vw, 0.92rem);
    margin-top: 4px;
    font-weight: 500;
}
.p360-hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    color: #bfdbfe;
    padding: 2px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-top: 6px;
    letter-spacing: 0.3px;
}

/* ── Profil Çubuğu ── */
.profil-bar {
    background: white;
    border-radius: 12px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 8px rgba(0,0,0,0.07);
    border-left: 4px solid #2563eb;
    margin-bottom: 14px;
}
.profil-bar-isim { font-weight: 800; font-size: 1rem; color: #0f172a; }
.profil-bar-detay { font-size: 0.8rem; color: #64748b; margin-top: 2px; }
.admin-badge { background: #fef2f2; color: #dc2626; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 6px; margin-left: 6px; }
.bakis-badge { background: #fef9c3; color: #854d0e; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; margin-left: 6px; }
.bildirim-dot { display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; margin-left: 4px; animation: blink 1.5s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── ANA MENÜ (Tab Benzeri, Mobil Uyumlu) ── */
.nav-container {
    background: white;
    border-radius: 12px;
    padding: 6px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    margin-bottom: 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
.nav-item {
    flex: 1;
    min-width: 80px;
    text-align: center;
    padding: 8px 6px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: clamp(0.65rem, 2vw, 0.82rem);
    color: #64748b;
    transition: all 0.18s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.nav-item:hover { background: #f1f5f9; color: #1e40af; }
.nav-item.aktif { background: #1e40af; color: white; box-shadow: 0 2px 8px rgba(30,64,175,0.3); }
.nav-item.aktif:hover { background: #1e3a8a; }

/* Alt Menü */
.subnav-container {
    background: #f1f5f9;
    border-radius: 10px;
    padding: 5px;
    margin-bottom: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
.subnav-item {
    flex: 1;
    min-width: 70px;
    text-align: center;
    padding: 7px 6px;
    border-radius: 7px;
    cursor: pointer;
    font-weight: 600;
    font-size: clamp(0.62rem, 1.8vw, 0.78rem);
    color: #475569;
    transition: all 0.15s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.subnav-item:hover { background: white; color: #1e40af; }
.subnav-item.aktif { background: white; color: #1e40af; box-shadow: 0 1px 4px rgba(0,0,0,0.1); font-weight: 800; }

/* ── Kartlar ── */
.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.06);
    border: 1px solid #f1f5f9;
}
.card:hover { box-shadow: 0 3px 16px rgba(0,0,0,0.09); }
.card-baslik {
    font-family: 'Lexend', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #1e40af;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid #dbeafe;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Stat Kartlar ── */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-box {
    background: white;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    border-top: 3px solid #2563eb;
}
.stat-box.g { border-top-color: #10b981; }
.stat-box.o { border-top-color: #f59e0b; }
.stat-box.r { border-top-color: #ef4444; }
.stat-box.p { border-top-color: #8b5cf6; }
.stat-num { font-family: 'Lexend', sans-serif; font-size: 1.8rem; font-weight: 800; color: #0f172a; line-height: 1; }
.stat-lbl { font-size: 0.72rem; color: #94a3b8; font-weight: 600; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.3px; }

/* ── Banner Mesajlar ── */
.banner { border-radius: 9px; padding: 11px 14px; margin-bottom: 12px; font-size: 0.875rem; font-weight: 500; }
.banner.info  { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
.banner.warn  { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }
.banner.ok    { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
.banner.err   { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }

/* ── Karne Kartı (Önizleme) ── */
.karne-preview {
    background: white;
    border: 2px solid #dbeafe;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 12px;
    position: relative;
    transition: box-shadow 0.2s;
}
.karne-preview:hover { box-shadow: 0 4px 20px rgba(37,99,235,0.12); }
.karne-preview.onaylandi { border-color: #10b981; background: #f0fdf4; }
.karne-preview.bekliyor  { border-color: #f59e0b; }
.karne-onay-rozet {
    position: absolute;
    top: 12px;
    right: 12px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
}
.rozet-onay    { background: #d1fae5; color: #065f46; }
.rozet-bekle   { background: #fef9c3; color: #854d0e; }
.rozet-yok     { background: #fee2e2; color: #991b1b; }
.karne-ogrenci { font-weight: 800; font-size: 0.95rem; color: #1e293b; }
.karne-detay   { font-size: 0.8rem; color: #64748b; margin-top: 3px; }
.karne-yorum   {
    background: #fefce8;
    border-left: 3px solid #f59e0b;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #78350f;
    margin-top: 10px;
    line-height: 1.6;
    cursor: pointer;
}
.karne-yorum:hover { background: #fef9c3; }

/* ── Davranış Notu Göstergesi ── */
.davranis-bar { height: 8px; border-radius: 4px; background: #e2e8f0; overflow: hidden; margin-top: 4px; }
.davranis-fill { height: 100%; border-radius: 4px; transition: width 0.4s; }

/* ── Puan Rozeti ── */
.puan-rozet {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 0.85rem;
}
.puan-rozet.iyi    { background: #d1fae5; color: #065f46; }
.puan-rozet.orta   { background: #fef9c3; color: #854d0e; }
.puan-rozet.dusuk  { background: #fee2e2; color: #991b1b; }
.puan-rozet.sifir  { background: #f1f5f9; color: #64748b; }

/* ── Kriter Kartı ── */
.kriter-card {
    background: #f0f9ff;
    padding: 10px 14px;
    border-radius: 9px;
    border-left: 4px solid #2563eb;
    margin-bottom: 8px;
}
.kriter-card .k-baslik { color: #1e3a8a; font-weight: 700; font-size: 0.88rem; }
.kriter-card .k-acik   { color: #94a3b8; font-size: 0.78rem; margin-top: 2px; }

/* ── Footer ── */
.app-footer {
    background: #0f172a;
    color: #94a3b8;
    border-radius: 12px;
    padding: 20px 28px;
    margin-top: 28px;
    text-align: center;
    font-size: 0.82rem;
    line-height: 1.7;
}
.app-footer a { color: #60a5fa; text-decoration: none; }

/* ── Streamlit Override ── */
[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
    background: #1e293b;
    border-radius: 10px;
    padding: 5px;
    gap: 4px;
}
[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button {
    background: transparent !important;
    color: #94a3b8 !important;
    border-radius: 7px !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
}
[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[aria-selected="true"] {
    background: #3b82f6 !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.35) !important;
}
div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
.stButton > button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; }

/* ── Mobil Medya Sorguları ── */
@media (max-width: 640px) {
    .block-container { padding: 0.5rem 0.5rem 2rem !important; }
    .nav-item { min-width: 60px; padding: 7px 4px; }
    .subnav-item { min-width: 55px; padding: 6px 4px; }
    .stat-grid { grid-template-columns: repeat(2, 1fr); }
    .profil-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
}

/* ── Öğretmen Listesi ── */
.ogrt-satir {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: box-shadow 0.15s;
}
.ogrt-satir:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.ogrt-satir.bekliyor { border-left: 4px solid #f59e0b; }
.ogrt-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 1rem;
    flex-shrink: 0;
}

/* ── Dönem Sekmesi ── */
.donem-chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 6px;
}
.donem-1 { background: #dbeafe; color: #1e40af; }
.donem-2 { background: #d1fae5; color: #065f46; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER
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

# Ana menü tanımları
ANA_MENU = [
    ("ogr_gorev",        "👥 Öğrenci & Görev"),
    ("ai_degerlendirme", "🤖 AI Değerlendirme"),
    ("raporlar",         "📊 Raporlar"),
    ("karne",            "📝 Karne Görüşleri"),
    ("yonetim",          "👨‍🏫 Yönetim"),
    ("ayarlar",          "⚙️ Ayarlar"),
]

# ==========================================
# 5. NAVİGASYON YARDIMCILARI
# ==========================================
def _init_nav():
    defaults = {
        "nav_ana": "ogr_gorev",
        "nav_ogr_alt": "excel_yukle",
        "nav_rapor_alt": "sinif_rapor",
        "nav_ayar_alt": "profil",
        "nav_sil_alt": "tekil_sil",
        "nav_karne_alt": "liste",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_main_nav(rol, admin_bakis):
    items = list(ANA_MENU)
    if rol != "admin" or admin_bakis:
        items = [i for i in items if i[0] != "yonetim"]

    aktif = st.session_state.get("nav_ana", "ogr_gorev")
    html = '<div class="nav-container">'
    for key, label in items:
        cls = "nav-item aktif" if aktif == key else "nav-item"
        html += f'<div class="{cls}" id="navbtn_{key}">{label}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Buton bazlı fallback (Streamlit state için)
    cols = st.columns(len(items))
    for col, (key, label) in zip(cols, items):
        is_a = aktif == key
        txt = f"◉ {label}" if is_a else label
        t = "primary" if is_a else "secondary"
        if col.button(txt, key=f"navmain_{key}", use_container_width=True, type=t):
            st.session_state["nav_ana"] = key
            st.rerun()

def render_sub_nav(items: list, state_key: str):
    aktif = st.session_state.get(state_key, items[0][0])
    cols  = st.columns(len(items))
    for col, (key, label) in zip(cols, items):
        is_a = aktif == key
        txt  = f"• {label}" if is_a else label
        t    = "primary" if is_a else "secondary"
        if col.button(txt, key=f"subnav_{state_key}_{key}", use_container_width=True, type=t):
            st.session_state[state_key] = key
            st.rerun()

# ==========================================
# 6. VERİTABANI
# ==========================================
def ayar_yukle():
    try:
        res = supabase.table('ayarlar').select('veri').eq('id', 1).execute()
        if res.data:
            data = res.data[0]['veri']
            if "sablonlar" not in data or not data["sablonlar"]:
                data["sablonlar"] = {SABLON_ADI: CEKIRDEK_SABLON}
            elif SABLON_ADI not in data["sablonlar"]:
                data["sablonlar"][SABLON_ADI] = CEKIRDEK_SABLON
            if "okullar" not in data or not data["okullar"]:
                data["okullar"] = DARGEÇIT_OKULLARI.copy()
            if "sistem_kilitli" not in data: data["sistem_kilitli"] = False
            if "otomatik_onay" not in data: data["otomatik_onay"] = True
            for k, v in data.get("kullanicilar", {}).items():
                if "onayli" not in v: v["onayli"] = True
                if "eposta" not in v: v["eposta"] = ""
            return data
        else:
            varsayilan = {
                "okullar": DARGEÇIT_OKULLARI.copy(),
                "sablonlar": {SABLON_ADI: CEKIRDEK_SABLON},
                "kullanicilar": {
                    "admin": {
                        "sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi",
                        "brans": "Tüm Dersler", "okul": "", "eposta": "saracaksan@gmail.com", "onayli": True
                    }
                },
                "sistem_kilitli": False,
                "otomatik_onay": True
            }
            supabase.table('ayarlar').insert({'id': 1, 'veri': varsayilan}).execute()
            return varsayilan
    except Exception as e:
        st.error(f"Ayarlar yüklenemedi: {e}")
        return {}

def ayar_kaydet(ayarlar):
    try:
        supabase.table('ayarlar').update({'veri': ayarlar}).eq('id', 1).execute()
    except Exception as e:
        st.error(f"Ayarlar kaydedilemedi: {e}")

@st.cache_data(ttl=0)
def veri_yukle():
    try:
        response = supabase.table('gorevler').select('*').execute()
        if not response.data:
            return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
        df = pd.DataFrame(response.data)
        df.rename(columns={
            'okul':'Okul','ekleyen':'Ekleyen','atanan_ogretmen':'Atanan_Ogretmen',
            'ders':'Ders','okul_no':'Okul No','ogrenci_adi_soyadi':'Öğrenci Adı Soyadı',
            'sinif':'Sınıf','gorev_turu':'Gorev_Turu','gorev_adi':'Gorev_Adi',
            'toplam_puan':'Toplam Puan','genel_degerlendirme_yorumu':'Genel Değerlendirme Yorumu',
            'dinamik_json':'Dinamik_JSON','donem':'Donem','onaylandi':'Onaylandi'
        }, inplace=True)
        if 'Dinamik_JSON' in df.columns:
            df['Dinamik_JSON'] = df['Dinamik_JSON'].apply(
                lambda x: json.dumps(x) if isinstance(x, dict) else (x if x else '{}')
            )
        if 'Donem'     not in df.columns: df['Donem']     = '1. Dönem'
        if 'Onaylandi' not in df.columns: df['Onaylandi'] = False
        return df
    except Exception as e:
        return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

# ==========================================
# 7. YARDIMCI FONKSİYONLAR
# ==========================================
def sifre_olustur(n=10):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))

def eposta_gonder(alici, konu, icerik):
    if not EMAIL_PASSWORD:
        return False, "EMAIL_PASSWORD tanımlı değil."
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'], msg['From'], msg['To'] = konu, EMAIL_SENDER, alici
        html = f"""<html><body style="font-family:Inter,Arial,sans-serif;background:#f8fafc;padding:20px;">
        <div style="background:white;border-radius:12px;padding:30px;max-width:500px;margin:0 auto;border-top:5px solid #2563eb;">
            <h2 style="color:#1e3a8a;margin:0 0 16px;">🧭 PUSULA 360</h2>
            <div style="color:#334155;line-height:1.7;">{icerik}</div>
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">
            <p style="color:#94a3b8;font-size:0.82rem;margin:0;">Bu e-posta otomatik gönderilmiştir.</p>
        </div></body></html>"""
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        s.login(EMAIL_SENDER, EMAIL_PASSWORD)
        s.sendmail(EMAIL_SENDER, alici, msg.as_string())
        s.quit()
        return True, "Gönderildi."
    except Exception as e:
        return False, str(e)

def bos_sablon_olustur():
    df = pd.DataFrame(columns=['Okul No','Öğrenci Adı Soyadı','Sınıf'])
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w:
        df.to_excel(w, index=False, sheet_name='Ogrenci_Listesi')
        w.sheets['Ogrenci_Listesi'].set_column(0, 2, 25)
    return out.getvalue()

def eokul_sablon_olustur():
    df = pd.DataFrame(columns=[
        'Öğrenci No','Adı Soyadı','Sınıfı','TÜRKÇE','MATEMATİK','HAYAT BİLGİSİ',
        'FEN BİLİMLERİ','SOSYAL BİLGİLER','İNGİLİZCE','DİN KÜLTÜRÜ VE AHLAK BİLGİSİ',
        'GÖRSEL SANATLAR','MÜZİK','BEDEN EĞİTİMİ VE SPOR','Davranış'
    ])
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w:
        df.to_excel(w, index=False, sheet_name='E_Okul_Karne')
    return out.getvalue()

def puan_cls(p):
    try:
        p = int(p)
        if p >= 85: return "iyi"
        elif p >= 65: return "orta"
        elif p > 0: return "dusuk"
        else: return "sifir"
    except:
        return "sifir"

def kriter_bul(k_id, ayarlar):
    for kriterler in ayarlar.get("sablonlar", {}).values():
        for k in kriterler:
            if k["id"] == k_id:
                return k["baslik"], k["max"], k.get("icon","📌")
    for k in CEKIRDEK_SABLON:
        if k["id"] == k_id:
            return k["baslik"], k["max"], k.get("icon","📌")
    return "Kriter", 100, "📌"

def isme_hitap_et(tam_isim):
    parcalar = str(tam_isim).strip().split()
    return " ".join(parcalar[:-1]) if len(parcalar) > 1 else tam_isim

def bildirim_sayisi(ayarlar):
    return sum(1 for v in ayarlar.get("kullanicilar", {}).values()
               if v.get("rol") == "ogretmen" and not v.get("onayli", True))

# ==========================================
# 8. HTML RAPOR ŞABLONLARİ
# ==========================================
def karne_onizleme_html(ad, sinif, okul_no, donem, davranis_notu, yorum, ders_notlari=None, okul_adi="", ogrt_ad=""):
    """Karne görüşü için profesyonel önizleme HTML'i"""
    dav = int(davranis_notu or 0)
    renge = "#10b981" if dav >= 85 else ("#f59e0b" if dav >= 65 else "#ef4444")
    durum = "Mükemmel Davranış" if dav >= 85 else ("Olumlu Davranış" if dav >= 65 else "Geliştirilmesi Gereken Davranış")

    notlar_html = ""
    if ders_notlari:
        notlar_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin:16px 0;'>"
        for ders, not_ in ders_notlari.items():
            ns = str(not_).strip()
            if ns and ns not in ["", "nan", "0.0", "0"]:
                try:
                    n_int = int(float(ns))
                    bg = "#dcfce7" if n_int >= 85 else ("#fef9c3" if n_int >= 65 else "#fee2e2")
                    tc = "#065f46" if n_int >= 85 else ("#854d0e" if n_int >= 65 else "#991b1b")
                    notlar_html += f"<div style='background:{bg};color:{tc};padding:6px 11px;border-radius:8px;font-size:0.82rem;font-weight:700;white-space:nowrap;'>{ders}: {n_int}</div>"
                except:
                    notlar_html += f"<div style='background:#f1f5f9;color:#475569;padding:6px 11px;border-radius:8px;font-size:0.82rem;font-weight:700;'>{ders}: {ns}</div>"
        notlar_html += "</div>"

    tarih = time.strftime('%d.%m.%Y')
    ilk_harf = ad[0].upper() if ad else "?"

    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Karne Görüşü — {ad}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',Arial,sans-serif;background:#f0f4f8;padding:20px;min-height:100vh;}}
  .karne{{background:white;max-width:700px;margin:0 auto;border-radius:18px;overflow:hidden;
          box-shadow:0 10px 50px rgba(0,0,0,0.13);}}
  .karne-header{{background:linear-gradient(135deg,#0c1e4a 0%,#1a3a8f 50%,#2563eb 100%);
                 color:white;padding:26px 30px;position:relative;overflow:hidden;}}
  .karne-header::after{{content:'';position:absolute;top:-40%;right:-5%;width:280px;height:280px;
    background:radial-gradient(circle,rgba(255,255,255,0.07) 0%,transparent 70%);pointer-events:none;}}
  .karne-header h1{{font-size:1.35rem;font-weight:800;margin-bottom:3px;}}
  .karne-header .okul{{font-size:0.83rem;opacity:0.75;margin-top:2px;}}
  .karne-body{{padding:26px 30px;}}
  .ogrenci-kart{{display:flex;align-items:center;gap:16px;background:#f0f9ff;
                 border-radius:13px;padding:16px 20px;margin-bottom:20px;border:1px solid #dbeafe;}}
  .avatar{{width:54px;height:54px;border-radius:50%;
           background:linear-gradient(135deg,#2563eb,#7c3aed);
           display:flex;align-items:center;justify-content:center;
           color:white;font-size:1.4rem;font-weight:800;flex-shrink:0;}}
  .ogrenci-bilgi h2{{font-size:1.05rem;font-weight:800;color:#1e293b;margin-bottom:2px;}}
  .ogrenci-bilgi p{{font-size:0.79rem;color:#64748b;}}
  .donem-badge{{display:inline-block;background:#dbeafe;color:#1e40af;
                padding:3px 10px;border-radius:6px;font-size:0.72rem;font-weight:800;margin-top:5px;}}
  .notlar-baslik{{font-size:0.78rem;font-weight:700;color:#64748b;text-transform:uppercase;
                  letter-spacing:0.5px;margin-bottom:8px;}}
  .davranis-blok{{background:#f8fafc;border-radius:10px;padding:14px 16px;margin:16px 0;
                  border:1px solid #e2e8f0;}}
  .davranis-ust{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}}
  .davranis-lbl{{font-size:0.8rem;font-weight:700;color:#374151;}}
  .davranis-puan{{font-size:1rem;font-weight:900;color:{renge};}}
  .davranis-durum{{display:inline-block;background:{renge}20;color:{renge};
                   font-size:0.72rem;font-weight:800;padding:2px 9px;border-radius:6px;}}
  .bar-bg{{height:10px;background:#e2e8f0;border-radius:5px;overflow:hidden;}}
  .bar-fill{{height:100%;border-radius:5px;background:{renge};width:{dav}%;transition:width 0.4s;}}
  .yorum-blok{{background:#fffbeb;border:1px solid #fde68a;border-radius:12px;
               padding:20px;margin-top:18px;}}
  .yorum-baslik{{display:flex;align-items:center;gap:8px;margin-bottom:12px;
                 color:#92400e;font-size:0.85rem;font-weight:800;}}
  .yorum-metin{{color:#78350f;font-size:0.93rem;line-height:1.78;white-space:pre-wrap;}}
  .imza{{display:flex;justify-content:space-between;align-items:flex-end;
         margin-top:22px;padding-top:16px;border-top:1px dashed #e2e8f0;}}
  .imza-ogrt{{font-size:0.82rem;color:#475569;}}
  .imza-ogrt strong{{display:block;font-size:0.9rem;color:#1e293b;}}
  .imza-tarih{{font-size:0.78rem;color:#94a3b8;}}
  .print-btn{{display:block;text-align:center;margin-top:18px;}}
  @media print{{
    body{{background:white;padding:0;}}
    .karne{{box-shadow:none;border-radius:0;max-width:100%;}}
    .print-btn{{display:none;}}
  }}
</style></head><body>
<div class="karne">
  <div class="karne-header">
    <h1>🧭 Dönem Sonu Karne Görüşü</h1>
    <div class="okul">{okul_adi or 'PUSULA 360'} &nbsp;·&nbsp; {donem}</div>
  </div>
  <div class="karne-body">
    <div class="ogrenci-kart">
      <div class="avatar">{ilk_harf}</div>
      <div class="ogrenci-bilgi">
        <h2>{ad}</h2>
        <p>Sınıf: <strong>{sinif}</strong> &nbsp;·&nbsp; Okul No: <strong>{okul_no}</strong></p>
        <span class="donem-badge">{donem}</span>
      </div>
    </div>
    {f'<div class="notlar-baslik">📊 Ders Notları</div>{notlar_html}' if notlar_html else ''}
    <div class="davranis-blok">
      <div class="davranis-ust">
        <span class="davranis-lbl">Davranış Notu</span>
        <span>
          <span class="davranis-puan">{dav}/100</span>
          &nbsp;<span class="davranis-durum">{durum}</span>
        </span>
      </div>
      <div class="bar-bg"><div class="bar-fill"></div></div>
    </div>
    <div class="yorum-blok">
      <div class="yorum-baslik">💬 Öğretmen Karne Görüşü</div>
      <div class="yorum-metin">{yorum if yorum else '<em style="color:#94a3b8">Görüş henüz yazılmamış.</em>'}</div>
    </div>
    <div class="imza">
      <div class="imza-ogrt">
        <strong>{ogrt_ad or 'Sınıf Öğretmeni'}</strong>
        Sınıf Öğretmeni
      </div>
      <div class="imza-tarih">PUSULA 360 &nbsp;·&nbsp; {tarih}</div>
    </div>
  </div>
</div>
<div class="print-btn">
  <button onclick="window.print()" style="background:#2563eb;color:white;border:none;
    padding:11px 28px;border-radius:9px;font-size:0.9rem;font-weight:700;cursor:pointer;
    box-shadow:0 4px 12px rgba(37,99,235,0.3);">
    🖨️ Yazdır / PDF Kaydet
  </button>
</div>
</body></html>"""

def ogrenci_karnesi_html_uret(df_ogrenci, ayarlar, tekil_gorev_idx=None):
    if tekil_gorev_idx is not None:
        df_islem = df_ogrenci.loc[[tekil_gorev_idx]]
    else:
        df_islem = df_ogrenci

    ogr_ad    = df_ogrenci.iloc[0].get('Öğrenci Adı Soyadı','')
    ogr_no    = df_ogrenci.iloc[0].get('Okul No','')
    ogr_sinif = df_ogrenci.iloc[0].get('Sınıf','')
    ogr_okul  = df_ogrenci.iloc[0].get('Okul','')

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{ogr_ad} - Karne</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f8fafc;margin:0;padding:20px;}}
  .page{{background:white;max-width:750px;margin:0 auto 28px;padding:28px;border-radius:14px;
          box-shadow:0 4px 20px rgba(0,0,0,0.07);border-top:6px solid #2563eb;page-break-inside:avoid;}}
  .header{{text-align:center;border-bottom:2px solid #e2e8f0;padding-bottom:14px;margin-bottom:18px;}}
  .header h1{{margin:0;color:#1e3a8a;font-size:1.6rem;}}
  .info-row{{display:flex;justify-content:space-between;background:#eff6ff;padding:14px;
             border-radius:10px;margin-bottom:20px;flex-wrap:wrap;gap:10px;}}
  .info-item{{text-align:center;}}
  .info-lbl{{font-size:0.72rem;color:#64748b;font-weight:700;text-transform:uppercase;}}
  .info-val{{font-size:1rem;color:#0f172a;font-weight:800;}}
  table{{width:100%;border-collapse:collapse;margin-bottom:18px;}}
  th,td{{padding:11px;text-align:left;border-bottom:1px solid #e2e8f0;}}
  th{{background:#f8fafc;color:#334155;font-size:0.82rem;font-weight:700;}}
  .puan-col{{text-align:center;font-weight:800;color:#2563eb;font-size:1rem;}}
  .yorum{{background:#fefce8;border:1px solid #fef08a;padding:14px;border-radius:10px;
           color:#854d0e;line-height:1.7;font-size:0.9rem;}}
  .imza{{margin-top:32px;text-align:right;color:#475569;font-size:0.85rem;}}
  @media print{{.page{{box-shadow:none;page-break-after:always;}}}}
</style></head><body>"""

    for idx, row in df_islem.iterrows():
        toplam  = int(pd.to_numeric(row.get('Toplam Puan',0), errors='coerce') or 0)
        dinamik = {}
        try:
            if pd.notna(row.get('Dinamik_JSON','')):
                dinamik = json.loads(str(row['Dinamik_JSON']))
        except: pass
        ders    = row.get('Ders','')
        ogrt_id = row.get('Atanan_Ogretmen','admin')
        ogrt_ad = ayarlar["kullanicilar"].get(ogrt_id,{}).get("ad","Öğretmen") if ogrt_id != "admin" else "Sistem Yöneticisi"

        html += f"""
<div class="page">
  <div class="header">
    <h1>{row.get('Gorev_Adi','Performans Görevi')}</h1>
    <p style="color:#64748b;margin:4px 0 0;">{ogr_okul} &nbsp;|&nbsp; {ders}</p>
  </div>
  <div class="info-row">
    <div class="info-item"><div class="info-lbl">Öğrenci</div><div class="info-val">{ogr_ad}</div></div>
    <div class="info-item"><div class="info-lbl">No / Sınıf</div><div class="info-val">{ogr_no} / {ogr_sinif}</div></div>
    <div class="info-item"><div class="info-lbl">Görev Türü</div><div class="info-val">{row.get('Gorev_Turu','')}</div></div>
    <div class="info-item"><div class="info-lbl">Toplam Puan</div><div class="info-val" style="color:#2563eb;font-size:1.3rem;">{toplam}</div></div>
  </div>
  <table>
    <tr><th style="width:30%">Kriter</th><th style="text-align:center;width:10%">Puan</th><th>Açıklama</th></tr>"""

        for k_id in [k.replace("_puan","") for k in dinamik if k.endswith("_puan")]:
            baslik, maks, icon = kriter_bul(k_id, ayarlar)
            html += f"<tr><td><strong>{icon} {baslik}</strong><br><small style='color:#94a3b8'>Max: {maks}</small></td><td class='puan-col'>{dinamik.get(f'{k_id}_puan',0)}</td><td style='font-size:0.88rem;color:#475569'>{dinamik.get(f'{k_id}_aciklama','-')}</td></tr>"

        html += f"""</table>
  <div class="yorum"><strong>💬 Öğretmen Görüşü:</strong><br><br>
    {row.get('Genel Değerlendirme Yorumu','Henüz yazılmamış.')}</div>
  <div class="imza"><strong>{ogrt_ad}</strong><br>{ders} Öğretmeni</div>
</div>"""

    html += "</body></html>"
    return html

def toplu_karne_html(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = """<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8">
<title>Sınıf Karneleri</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f8fafc;margin:0;padding:20px;}}
  .page{{background:white;max-width:720px;margin:0 auto 24px;padding:22px;border-radius:14px;
          box-shadow:0 4px 20px rgba(0,0,0,0.08);border-top:7px solid #2563eb;page-break-after:always;}}
  .header{{background:linear-gradient(135deg,#0c1e4a,#2563eb);color:white;padding:16px 20px;border-radius:10px;
           display:flex;justify-content:space-between;align-items:center;}}
  .puan-daire{{font-size:1.8rem;font-weight:900;background:white;color:#2563eb;
               padding:4px 14px;border-radius:8px;}}
  .info-box{{display:flex;flex-wrap:wrap;gap:14px;margin-top:14px;padding:12px;
             background:#eff6ff;border-radius:10px;border-left:4px solid #3b82f6;}}
  .info-item{{display:flex;flex-direction:column;}}
  .info-lbl{{font-size:0.7rem;color:#64748b;font-weight:700;text-transform:uppercase;}}
  .info-val{{font-size:0.95rem;font-weight:800;color:#0f172a;}}
  table{{width:100%;border-collapse:collapse;margin-top:16px;}}
  th{{background:#f1f5f9;color:#1e293b;padding:10px;font-size:0.8rem;border-bottom:2px solid #cbd5e1;}}
  td{{padding:10px;border-bottom:1px solid #e2e8f0;font-size:0.85rem;}}
  .yorum{{background:#fffbeb;padding:14px;margin-top:16px;border-radius:10px;
           border-left:5px solid #f59e0b;color:#78350f;font-size:0.9rem;line-height:1.65;}}
  .imza{{text-align:right;margin-top:20px;color:#475569;padding-top:10px;border-top:1px dashed #cbd5e1;font-size:0.85rem;}}
  @media print{{.page{{box-shadow:none;}}}}
</style></head><body>"""

    for _, b in df_sinif.iterrows():
        toplam  = int(pd.to_numeric(b.get('Toplam Puan',0), errors='coerce') or 0)
        dinamik = {}
        try:
            if pd.notna(b.get('Dinamik_JSON','')):
                dinamik = json.loads(str(b['Dinamik_JSON']))
        except: pass

        html += f"""<div class="page">
  <div class="header">
    <div><div style="opacity:0.75;font-size:0.8rem">{b.get('Okul','')}</div>
         <h3 style="margin:2px 0">{b.get('Gorev_Adi','')} ({b.get('Ders',ogrt_brans)})</h3></div>
    <div style="text-align:center"><div class="puan-daire">{toplam}</div>
         <div style="font-size:0.68rem;margin-top:2px;font-weight:700">/ 100</div></div>
  </div>
  <div class="info-box">
    <div class="info-item"><span class="info-lbl">Öğrenci</span><span class="info-val">{b.get('Öğrenci Adı Soyadı','')}</span></div>
    <div class="info-item"><span class="info-lbl">Sınıf</span><span class="info-val">{b.get('Sınıf','')}</span></div>
    <div class="info-item"><span class="info-lbl">No</span><span class="info-val">{b.get('Okul No','')}</span></div>
    <div class="info-item"><span class="info-lbl">Görev Türü</span><span class="info-val">{b.get('Gorev_Turu','')}</span></div>
  </div>
  <table><tr><th style="width:28%">Kriter</th><th style="text-align:center;width:8%">Max</th>
  <th style="text-align:center;width:8%">Alınan</th><th>Açıklama</th></tr>"""

        for k in aktif_kriterler:
            p = dinamik.get(f"{k['id']}_puan", 0)
            a = dinamik.get(f"{k['id']}_aciklama", "-")
            html += f"<tr><td><strong>{k.get('icon','')} {k['baslik']}</strong></td><td style='text-align:center'>{k['max']}</td><td style='text-align:center;font-weight:800;color:#2563eb'>{p}</td><td style='font-size:0.82rem'>{a}</td></tr>"

        html += f"""</table>
  <div class="yorum"><strong>💬 Genel Yorum:</strong><br><br>{b.get('Genel Değerlendirme Yorumu','Bekleniyor.')}</div>
  <div class="imza"><strong>{ogrt_ad}</strong><br>{b.get('Ders',ogrt_brans)} Öğretmeni</div>
</div>"""

    html += "</body></html>"
    return html

def sinif_analiz_html(df_sinif, sinif_adi, ogrt_ad):
    df_p = df_sinif.copy()
    df_p['Toplam Puan'] = pd.to_numeric(df_p['Toplam Puan'], errors='coerce').fillna(0)
    ort  = round(df_p['Toplam Puan'].mean(), 1)
    maks = int(df_p['Toplam Puan'].max())
    minn = int(df_p['Toplam Puan'].min())
    sifir = len(df_p[df_p['Toplam Puan']==0])
    iyi   = len(df_p[df_p['Toplam Puan']>=85])
    orta  = len(df_p[(df_p['Toplam Puan']>=65)&(df_p['Toplam Puan']<85)])
    dusuk = len(df_p[df_p['Toplam Puan']<65])
    n = max(1, len(df_p[df_p['Toplam Puan']>0]))

    html = f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8">
<title>{sinif_adi} Analiz</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f8fafc;margin:0;padding:20px;}}
  .c{{max-width:900px;margin:0 auto;}}
  .hero{{background:linear-gradient(135deg,#0c1e4a,#2563eb);color:white;padding:22px 28px;border-radius:14px;margin-bottom:18px;}}
  .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:18px;}}
  .stat{{background:white;border-radius:12px;padding:14px;text-align:center;box-shadow:0 1px 6px rgba(0,0,0,0.06);}}
  .sn{{font-size:2rem;font-weight:900;}}.sl{{font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;}}
  .bar-s{{background:white;border-radius:12px;padding:18px;margin-bottom:18px;box-shadow:0 1px 6px rgba(0,0,0,0.06);}}
  .bar-r{{display:flex;align-items:center;gap:12px;margin-bottom:10px;}}
  .bar-l{{width:160px;font-size:0.82rem;font-weight:700;color:#334155;}}
  .bar-t{{flex:1;background:#e2e8f0;border-radius:5px;height:20px;overflow:hidden;}}
  .bar-f{{height:100%;border-radius:5px;display:flex;align-items:center;padding-left:8px;color:white;font-size:0.75rem;font-weight:700;}}
  table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,0.06);}}
  th{{background:#1e3a8a;color:white;padding:11px;font-size:0.82rem;text-align:left;}}
  td{{padding:10px 12px;border-bottom:1px solid #e2e8f0;font-size:0.85rem;}}
  .badge{{display:inline-block;padding:3px 9px;border-radius:10px;font-size:0.75rem;font-weight:700;}}
  .bg{{background:#d1fae5;color:#065f46;}}.bo{{background:#fef9c3;color:#854d0e;}}.br{{background:#fee2e2;color:#991b1b;}}
  .footer{{text-align:center;color:#94a3b8;font-size:0.78rem;margin-top:18px;padding:14px;background:white;border-radius:10px;}}
</style></head><body><div class="c">
<div class="hero">
  <h2 style="margin:0">{sinif_adi} — Değerlendirme Analiz Raporu</h2>
  <p style="margin:5px 0 0;opacity:0.8">{ogrt_ad} &nbsp;|&nbsp; {time.strftime('%d.%m.%Y %H:%M')}</p>
</div>
<div class="stats">
  <div class="stat"><div class="sn" style="color:#2563eb">{len(df_sinif)}</div><div class="sl">Toplam Öğrenci</div></div>
  <div class="stat"><div class="sn" style="color:#10b981">{ort}</div><div class="sl">Ortalama</div></div>
  <div class="stat"><div class="sn" style="color:#059669">{maks}</div><div class="sl">En Yüksek</div></div>
  <div class="stat"><div class="sn" style="color:#ef4444">{minn}</div><div class="sl">En Düşük</div></div>
  <div class="stat"><div class="sn" style="color:#f59e0b">{sifir}</div><div class="sl">Değerlendirilmemiş</div></div>
</div>
<div class="bar-s">
  <h3 style="margin:0 0 14px;color:#1e3a8a">Başarı Dağılımı</h3>
  <div class="bar-r"><div class="bar-l">🟢 Başarılı (85+)</div>
    <div class="bar-t"><div class="bar-f" style="width:{round(iyi/n*100)}%;background:#10b981">{iyi} öğrenci</div></div></div>
  <div class="bar-r"><div class="bar-l">🟡 Orta (65-84)</div>
    <div class="bar-t"><div class="bar-f" style="width:{round(orta/n*100)}%;background:#f59e0b">{orta} öğrenci</div></div></div>
  <div class="bar-r"><div class="bar-l">🔴 Gelişmeli (&lt;65)</div>
    <div class="bar-t"><div class="bar-f" style="width:{round(dusuk/n*100)}%;background:#ef4444">{dusuk} öğrenci</div></div></div>
</div>
<table><tr><th>#</th><th>No</th><th>Öğrenci</th><th>Sınıf</th><th>Görev</th><th>Puan</th><th>Durum</th></tr>"""

    df_s = df_sinif.copy()
    df_s['Toplam Puan'] = pd.to_numeric(df_s['Toplam Puan'], errors='coerce').fillna(0)
    df_s = df_s.sort_values('Toplam Puan', ascending=False)
    for i, (_, row) in enumerate(df_s.iterrows(), 1):
        p = int(row.get('Toplam Puan', 0))
        b = 'bg' if p>=85 else ('bo' if p>=65 else 'br')
        d = 'Başarılı' if p>=85 else ('Orta' if p>=65 else ('Gelişmeli' if p>0 else 'Bekliyor'))
        html += f"<tr><td>{i}</td><td>{row.get('Okul No','')}</td><td><strong>{row.get('Öğrenci Adı Soyadı','')}</strong></td><td>{row.get('Sınıf','')}</td><td>{row.get('Gorev_Adi','')}</td><td style='font-weight:800'>{p}</td><td><span class='badge {b}'>{d}</span></td></tr>"

    html += f"""</table>
<div class="footer">PUSULA 360 &nbsp;|&nbsp; {time.strftime('%d.%m.%Y')} &nbsp;|&nbsp;
  Tasarım: <strong>Sıraç AKSAN</strong></div>
</div></body></html>"""
    return html

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

    if mod == "A":
        prompt += f'Yorumdan puan üret. Not: "{ham_metin}"'
    elif mod == "B":
        prompt += f"Hedef {hedef_puan}/100 olacak şekilde kriterlere puan dağıt."
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
    """Gerçek öğretmen diliyle karne görüşü yazar. Davranış notuna göre ton ayarlar."""
    ogrenci_isim = isme_hitap_et(tam_isim)
    dav = int(float(str(davranis_notu or 70)))

    # Ders notlarını analiz et
    basarili_dersler, gelismeli_dersler = [], []
    tum_notlar_metni = ""
    for ders, n in notlar_dict.items():
        ns = str(n).strip()
        if ns and ns not in ["","nan","0.0","0"]:
            tum_notlar_metni += f"  - {ders}: {ns}/100\n"
            try:
                n_int = int(float(ns))
                if n_int >= 85:
                    basarili_dersler.append(ders)
                elif n_int < 65:
                    gelismeli_dersler.append(ders)
            except: pass

    # Davranış durumu ve ton belirleme
    if dav >= 90:
        dav_yorum = "son derece olumlu, örnek teşkil eden"
        dav_ton   = "övgü dolu ve motive edici"
        dav_ornek = "arkadaşlarına karşı saygılı, sorumluluklarını eksiksiz yerine getiren, derslere aktif katılan"
    elif dav >= 80:
        dav_yorum = "olumlu ve takdire değer"
        dav_ton   = "teşvik edici ve onaylayıcı"
        dav_ornek = "kurallara uyan, arkadaşlarıyla uyumlu, sorumluluk sahibi"
    elif dav >= 65:
        dav_yorum = "gelişim gösteren ve ortalama düzeyde"
        dav_ton   = "yapıcı, dengeli, gelişime açık"
        dav_ornek = "zaman zaman uyarı gerektiren ancak genel olarak uyumlu"
    elif dav >= 50:
        dav_yorum = "geliştirilmesi gereken"
        dav_ton   = "uyarıcı ama umut verici, yapıcı"
        dav_ornek = "kurallara uymada güçlük yaşayan, öz denetim becerilerini geliştirmesi gereken"
    else:
        dav_yorum = "ciddi şekilde geliştirilmesi gereken"
        dav_ton   = "endişe içeren ama çözüm odaklı, aile iş birliğini vurgulayan"
        dav_ornek = "tutum ve davranışlarında köklü değişime ihtiyaç duyan"

    basarili_str   = ", ".join(basarili_dersler)   if basarili_dersler   else "belirli alanlarda"
    gelismeli_str  = ", ".join(gelismeli_dersler)  if gelismeli_dersler  else ""

    prompt = f"""Sen deneyimli bir sınıf öğretmenisin. Adın {ogrt_ad}.
{sinif} sınıfı öğrencisi {tam_isim} için dönem sonu karne görüşü yazacaksın.

ÖĞRENCİNİN DERS NOTLARI (100 üzerinden):
{tum_notlar_metni if tum_notlar_metni else "  (Not bilgisi girilmemiş)"}

DAVRANIŞ NOTU: {dav}/100 ({dav_yorum} davranış)
Davranış tonu: {dav_ton}
Davranış örnek ifade: {dav_ornek}

BAŞARILI OLDUĞU DERSLER: {basarili_str}
GELİŞTİRMESİ GEREKEN DERSLER: {gelismeli_str if gelismeli_str else "Yok"}
ÖĞRETMEN ÖZEL GÖZLEM: {ekstra_gozlem if ekstra_gozlem else "Ek gözlem yok."}

YAZIM KURALLARI — BUNLARA KESINLIKLE UY:
1. "Sevgili {ogrenci_isim}," diye başla — soyadını asla kullanma
2. Davranış notu {dav}/100 olduğu için ton {dav_ton} olmalı
3. Davranış ile ilgili somut gözlem cümlesi yaz ({dav_ornek})
4. Akademik başarıyı değerlendir: {'güçlü dersleri özellikle öv' if basarili_dersler else 'genel gayretini değerlendir'}
5. {'Gelişmesi gereken derslere nazikçe dikkat çek ve destek söz ver' if gelismeli_dersler else ''}
6. Son cümle aileye hitap etsin: veli teşekkürü veya iş birliği daveti
7. 4-5 cümle — kısa değil, dolu ve gerçek öğretmen diliyle
8. Cümleleri birbirine bağla, liste değil akıcı paragraf
9. Sıcak, samimi, resmi ama kalp koyan bir dil — klişeden kaçın
10. Türkçe yazım kurallarına dikkat et

SADECE görüş metnini yaz. Başlık, açıklama, tırnak işareti ekleme."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "text/plain",
            "temperature": 0.85,
            "maxOutputTokens": 400
        }
    }
    r = requests.post(GEMINI_API_URL, headers={"Content-Type":"application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def ai_toplu_karne_yaz(ogrenci_listesi, ogrt_ad):
    """Tüm sınıfa toplu karne görüşü yazar"""
    sonuclar = {}
    for ogr in ogrenci_listesi:
        try:
            gorüş = ai_karne_gorusu_yaz(
                ogr["ad"], ogr["sinif"], ogr["notlar"],
                ogr.get("davranis", 75), ogr.get("gozlem",""), ogrt_ad
            )
            sonuclar[ogr["okul_no"]] = gorüş
            time.sleep(0.3)  # Rate limit
        except Exception as e:
            sonuclar[ogr["okul_no"]] = f"[HATA: {e}]"
    return sonuclar

# ==========================================
# 10. ŞABLON YÖNETİMİ
# ==========================================
def sablon_yonetimi_ui(ayarlar, kb, rol):
    st.markdown("#### 📐 Değerlendirme Ölçeği Yönetimi")
    st.markdown('<div class="banner info">Kriterlerin toplam puanı 100 olmalıdır.</div>', unsafe_allow_html=True)

    t_man, t_ex = st.tabs(["✍️ Manuel Oluştur", "📥 Excel ile Yükle"])
    with t_man:
        s_isim = st.text_input("Şablon Adı", key=f"man_ad_{rol}")
        if "t_df" not in st.session_state:
            st.session_state["t_df"] = pd.DataFrame([{"Başlık":"İçerik","Puan":50,"Açıklama":""}])
        e_df = st.data_editor(st.session_state["t_df"], num_rows="dynamic", use_container_width=True, key=f"man_ed_{rol}")
        if st.button("💾 Kaydet", key=f"man_kaydet_{rol}"):
            if pd.to_numeric(e_df["Puan"], errors="coerce").sum() == 100 and s_isim:
                tam = s_isim if rol=="admin" else f"{s_isim} (Ekleyen: {kb['ad']})"
                n_k = [{"id":f"k{i+1}","baslik":str(r["Başlık"]),"max":int(r["Puan"]),
                         "icon":"📌","aciklama":str(r.get("Açıklama",""))} for i,r in e_df.iterrows()]
                ayarlar["sablonlar"][tam] = n_k
                ayar_kaydet(ayarlar)
                st.success("✅ Kaydedildi!")
                st.rerun()
            else:
                st.error("Toplam 100 olmalı ve isim girilmeli!")

    with t_ex:
        sab = pd.DataFrame(columns=["Kriter Başlığı","Maksimum Puan","Açıklama"])
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as w:
            sab.to_excel(w, index=False)
        st.download_button("📄 Excel Şablonu İndir", data=out.getvalue(), file_name="Olcek_Sablonu.xlsx")
        up = st.file_uploader("Doldurulmuş Excel Yükle", type=["xlsx"], key=f"up_sab_{rol}")
        up_isim = st.text_input("Ölçek Adı", key=f"up_ad_{rol}")
        if st.button("🚀 Yükle", key=f"ex_kaydet_{rol}"):
            if up and up_isim:
                try:
                    sdf = pd.read_excel(up)
                    if pd.to_numeric(sdf.iloc[:,1], errors="coerce").sum() == 100:
                        tam = up_isim if rol=="admin" else f"{up_isim} (Ekleyen: {kb['ad']})"
                        n_k = [{"id":f"k{i+1}","baslik":str(r.iloc[0]),"max":int(r.iloc[1]),
                                  "icon":"📌","aciklama":str(r.iloc[2]) if len(r)>2 else ""} for i,r in sdf.iterrows()]
                        ayarlar["sablonlar"][tam] = n_k
                        ayar_kaydet(ayarlar)
                        st.success("✅ Yüklendi!")
                        st.rerun()
                    else:
                        st.error("Toplam 100 olmalı!")
                except Exception as e:
                    st.error(f"Hata: {e}")

    st.markdown("---")
    st.markdown("**🗑️ Ölçek Sil**")
    silinebilir = [s for s in ayarlar["sablonlar"] if "Varsayılan" not in s and
                   (rol=="admin" or f"(Ekleyen: {kb['ad']})" in s)]
    if silinebilir:
        sil_s = st.selectbox("Silinecek", silinebilir)
        if st.button("🗑️ Sil", key=f"sil_sab_{rol}"):
            del ayarlar["sablonlar"][sil_s]
            ayar_kaydet(ayarlar)
            st.success("Silindi.")
            st.rerun()
    else:
        st.info("Silinebilecek şablon yok.")

# ==========================================
# 11. KULLANIM KILAVUZU
# ==========================================
def kullanim_kilavuzu():
    with st.expander("📖 Hızlı Başlangıç Kılavuzu", expanded=False):
        st.markdown("""
**1. Öğrenci Yükleme:** Öğrenci & Görev → Excel ile Yükle → Şablon indir, doldur, yükle.

**2. AI Değerlendirme:** AI Değerlendirme sekmesinde öğrenci seç → Mod A/B/C ile puan üret → Kaydet.
- Mod A: Yorum gir → AI puanlasın
- Mod B: Hedef puan ver → AI dağıtsın  
- Mod C: Manuel puan → AI açıklasın

**3. Karne Görüşleri:** Karne sekmesine git → Not listesini yükle → Tekil veya toplu AI görüş üret → Onayla → Arşivle.

**4. Raporlar:** Raporlar sekmesinden HTML karne, analiz raporu ve Excel çizelge indir.

**5. Öğrenci Sorgulama:** Giriş yapmadan okul no ile karne sorgulama yapılabilir.
        """)

# ==========================================
# 12. ÖĞRENCİ SORGU EKRANI
# ==========================================
def ogrenci_sorgu_ekrani(df, ayarlar):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<div class='card-baslik'>🔍 Öğrenci Karne Sorgulama</div>", unsafe_allow_html=True)
    st.markdown('<div class="banner info">Okul numaranızı girerek karne ve değerlendirme sonuçlarınıza ulaşabilirsiniz.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1,1])
    okul_listesi = sorted(df['Okul'].dropna().unique()) if not df.empty else []
    s_okul  = c1.selectbox("🏫 Okul", ["— Seçiniz —"] + list(okul_listesi))
    siniflar = sorted(df[df['Okul']==s_okul]['Sınıf'].dropna().unique()) if s_okul != "— Seçiniz —" else []
    s_sinif = c2.selectbox("📚 Sınıf", ["—"] + siniflar if siniflar else ["Önce okul seçin"])
    s_no    = st.text_input("🔢 Okul Numaranız")

    if st.button("🔍 Sonuçlarımı Getir", use_container_width=True, type="primary"):
        if s_okul == "— Seçiniz —" or not s_no.strip():
            st.warning("Okul ve okul numarası zorunludur.")
        else:
            filtre = (df['Okul']==s_okul) & (df['Okul No']==s_no.strip())
            if s_sinif not in ["—","Önce okul seçin"]:
                filtre = filtre & (df['Sınıf']==s_sinif)
            sonuclar = df[filtre]

            if sonuclar.empty:
                st.error("❌ Kayıt bulunamadı. Okul numaranızı ve okulunuzu kontrol edin.")
            else:
                ad = sonuclar.iloc[0]['Öğrenci Adı Soyadı']
                st.markdown(f'<div class="banner ok">👋 Hoş geldin, <strong>{ad}</strong>! {len(sonuclar)} adet kayıt bulundu.</div>', unsafe_allow_html=True)

                # Karne görüşleri (Gorev_Turu == Karne Gorusu) için özel gösterim
                karne_kayitlari = sonuclar[sonuclar['Gorev_Turu']=='Karne Gorusu']
                for _, krow in karne_kayitlari.iterrows():
                    yorum = krow.get('Genel Değerlendirme Yorumu','')
                    notlar = {}
                    try:
                        djson = json.loads(str(krow.get('Dinamik_JSON','{}')))
                        notlar = djson.get('notlar', {})
                        davranis = notlar.get('Davranış', 75)
                    except:
                        davranis = 75
                    if yorum:
                        st.markdown(f"""
                        <div class="karne-preview onaylandi">
                            <div class="karne-onay-rozet rozet-onay">✅ Onaylı Karne Görüşü</div>
                            <div class="karne-ogrenci">{ad}</div>
                            <div class="karne-detay">{krow.get('Gorev_Adi','')} · {krow.get('Sınıf','')} Sınıfı</div>
                            <div class="karne-yorum">{yorum}</div>
                        </div>""", unsafe_allow_html=True)

                # Performans görevleri
                gorev_kayitlari = sonuclar[sonuclar['Gorev_Turu']!='Karne Gorusu']
                toplu_html = ogrenci_karnesi_html_uret(gorev_kayitlari if not gorev_kayitlari.empty else sonuclar, ayarlar)
                st.download_button("📥 Tüm Karnemi İndir", data=toplu_html,
                                   file_name=f"{ad}_Karne.html", mime="text/html", use_container_width=True)

                for idx, row in gorev_kayitlari.iterrows():
                    p = int(pd.to_numeric(row.get('Toplam Puan',0), errors='coerce') or 0)
                    with st.expander(f"📌 {row['Ders']} — {row['Gorev_Adi']} — {p}/100"):
                        st.markdown(f'<span class="puan-rozet {puan_cls(p)}">{p} / 100</span>', unsafe_allow_html=True)
                        if row.get('Genel Değerlendirme Yorumu'):
                            st.markdown(f'<div class="banner warn">💬 {row["Genel Değerlendirme Yorumu"]}</div>', unsafe_allow_html=True)
                        dinamik = {}
                        try:
                            dinamik = json.loads(str(row.get('Dinamik_JSON','{}')))
                        except: pass
                        if dinamik:
                            for k_id in [k.replace("_puan","") for k in dinamik if k.endswith("_puan")]:
                                baslik, maks, _ = kriter_bul(k_id, ayarlar)
                                st.markdown(f"- **{baslik}**: {dinamik.get(f'{k_id}_puan',0)}/{maks} — {dinamik.get(f'{k_id}_aciklama','')}")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 13. GİRİŞ EKRANI
# ==========================================
def giris_ekrani(df, ayarlar):
    tab_ogr, tab_ogrt = st.tabs(["🎓 Öğrenci / Veli Girişi", "👨‍🏫 Öğretmen / İdare Girişi"])

    with tab_ogr:
        ogrenci_sorgu_ekrani(df, ayarlar)

    with tab_ogrt:
        c1, c2, c3 = st.columns([1,1.8,1])
        with c2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            g1, g2, g3 = st.tabs(["🔐 Giriş Yap","📝 Kayıt Ol","🔑 Şifremi Unuttum"])

            with g1:
                if ayarlar.get("sistem_kilitli",False):
                    st.markdown('<div class="banner err">🔒 Sistem öğretmen girişine kapatılmıştır.</div>', unsafe_allow_html=True)
                k_adi = st.text_input("Kullanıcı Adı", key="l_kadi")
                sifre = st.text_input("Şifre", type="password", key="l_sifre")
                if st.button("Giriş Yap →", use_container_width=True, type="primary", key="btn_giris"):
                    user = ayarlar["kullanicilar"].get(k_adi)
                    if user and user["sifre"] == sifre:
                        if user.get("rol") != "admin" and not user.get("onayli",True):
                            st.warning("⏳ Hesabınız yönetici onayı bekliyor.")
                        elif ayarlar.get("sistem_kilitli",False) and user.get("rol") != "admin":
                            st.error("🔒 Sistem kilitli.")
                        else:
                            st.session_state.update({
                                "giris_yapti": True,
                                "aktif_kullanici": k_adi,
                                "kullanici_bilgi": user,
                                "admin_bakis_modu": False,
                                "admin_bakis_ogretmen": None
                            })
                            st.rerun()
                    else:
                        st.error("❌ Hatalı kullanıcı adı veya şifre!")

            with g2:
                st.markdown('<div class="banner info">💡 Aynı okulda zaten kaydınız varsa yeniden kayıt yapmayın. Şifrenizi idareden alın.</div>', unsafe_allow_html=True)
                sec_il = st.selectbox("İl", ["— Seçiniz —"] + TUM_ILLER)
                sec_ilce = ""
                if sec_il != "— Seçiniz —":
                    sec_ilce = st.text_input(f"{sec_il} — İlçe").strip().title()
                sec_okul = "— Seçiniz —"
                if sec_ilce:
                    sec_okul = st.selectbox("Okul", ["— Seçiniz —","➕ Yeni Okul"] + sorted(ayarlar["okullar"]))
                    if sec_okul == "➕ Yeni Okul":
                        yeni_ok = st.text_input("Okul Adı").strip().title()
                        if yeni_ok:
                            sec_okul = f"{sec_il} / {sec_ilce} / {yeni_ok}"
                r_ad     = st.text_input("Ad Soyad")
                r_brans  = st.text_input("Branş")
                r_eposta = st.text_input("E-posta", placeholder="ornek@gmail.com")
                r_kadi   = st.text_input("Kullanıcı Adı")
                r_sifre  = st.text_input("Şifre", type="password")
                mevcut = any(
                    str(v.get("ad","")).strip().lower()==str(r_ad).strip().lower() and v.get("okul")==sec_okul
                    for v in ayarlar["kullanicilar"].values()
                )
                if st.button("Kayıt Ol", use_container_width=True, type="primary"):
                    if r_kadi in ayarlar["kullanicilar"]:
                        st.error("Bu kullanıcı adı alınmış.")
                    elif mevcut:
                        st.error("⚠️ Bu okulda adınıza kayıt mevcut! İdarenizden şifre alın.")
                    elif not (r_kadi and r_sifre and r_ad and "Seçiniz" not in sec_okul):
                        st.warning("Tüm alanları doldurun.")
                    else:
                        if sec_okul not in ayarlar["okullar"]:
                            ayarlar["okullar"].append(sec_okul)
                        is_auto = ayarlar.get("otomatik_onay",True)
                        ayarlar["kullanicilar"][r_kadi] = {
                            "sifre":r_sifre,"rol":"ogretmen","ad":r_ad,"okul":sec_okul,
                            "brans":r_brans,"eposta":r_eposta,"onayli":is_auto
                        }
                        ayar_kaydet(ayarlar)
                        if is_auto:
                            st.success("✅ Kayıt başarılı! Giriş yapabilirsiniz.")
                        else:
                            st.success("⏳ Kayıt alındı. Yönetici onayı bekleniyor.")

            with g3:
                u_eposta = st.text_input("Kayıtlı E-posta Adresiniz")
                if st.button("🔑 Yeni Şifre Gönder", use_container_width=True):
                    bulunan, bk = None, None
                    for k, u in ayarlar["kullanicilar"].items():
                        if u.get("eposta","").strip().lower() == u_eposta.strip().lower():
                            bulunan, bk = u, k
                            break
                    if not bulunan:
                        st.error("Bu e-posta ile kayıtlı kullanıcı bulunamadı.")
                    else:
                        yeni = sifre_olustur()
                        ok, msg = eposta_gonder(u_eposta, "PUSULA 360 — Yeni Şifreniz",
                            f"Sayın {bulunan['ad']},<br><br>Yeni şifreniz: <strong>{yeni}</strong>")
                        if ok:
                            ayarlar["kullanicilar"][bk]["sifre"] = yeni
                            ayar_kaydet(ayarlar)
                            st.success("✅ Yeni şifre gönderildi.")
                        else:
                            st.error(f"Gönderilemedi: {msg}")
                            st.info(f"Manuel şifre: **{yeni}**")
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

    # ── Profil çubuğu ──
    c_profil, c_cikis = st.columns([5,1])
    bildirim = bildirim_sayisi(ayarlar)
    with c_profil:
        admin_badge = '<span class="admin-badge">ADMİN</span>' if rol=="admin" and not admin_bakis else ""
        bakis_badge = f'<span class="bakis-badge">👁 GÖZATMA → {admin_bakis_ogrt}</span>' if admin_bakis else ""
        bil_dot     = f'<span class="bildirim-dot"></span>' if bildirim>0 and rol=="admin" and not admin_bakis else ""
        st.markdown(f"""
        <div class="profil-bar">
            <div>
                <div class="profil-bar-isim">{'👁 ' if admin_bakis else '👋 '}{kb['ad']} {admin_badge} {bakis_badge} {bil_dot}</div>
                <div class="profil-bar-detay">{kb.get('okul','') or 'Sistem Yöneticisi'} &nbsp;·&nbsp; {kb.get('brans','')}
                    {f' &nbsp;·&nbsp; <strong>{bildirim} onay bekliyor</strong>' if bildirim>0 and rol=="admin" and not admin_bakis else ''}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c_cikis:
        if admin_bakis:
            if st.button("← Admin'e Dön", use_container_width=True):
                st.session_state["admin_bakis_modu"] = False
                st.session_state["admin_bakis_ogretmen"] = None
                st.rerun()
        else:
            if st.button("🚪 Çıkış", use_container_width=True):
                st.session_state.clear()
                st.rerun()

    # ── Yetki filtresi ──
    if admin_bakis and admin_bakis_ogrt:
        kb_b = ayarlar["kullanicilar"].get(admin_bakis_ogrt, kb)
        df_yetkili = df[(df['Okul']==kb_b.get("okul")) &
                        ((df['Atanan_Ogretmen']==admin_bakis_ogrt)|(df['Atanan_Ogretmen']=='admin'))]
    elif rol == "admin":
        df_yetkili = df
    else:
        df_yetkili = df[(df['Okul']==kb.get("okul")) &
                        ((df['Atanan_Ogretmen']==aktif_id)|(df['Atanan_Ogretmen']=='admin'))]

    kullanim_kilavuzu()
    render_main_nav(rol, admin_bakis)
    aktif_ana = st.session_state.get("nav_ana","ogr_gorev")

    # ══════════════════════════════════════════════════
    # SEKME: ÖĞRENCİ & GÖREV
    # ══════════════════════════════════════════════════
    if aktif_ana == "ogr_gorev":
        ALT = [
            ("excel_yukle",    "📥 Excel Yükle"),
            ("tekil_ekle",     "➕ Tekil Ekle"),
            ("havuz_ata",      "🏫 Havuzdan Ata"),
            ("gecmis_duzenle", "✏️ Geçmişi Düzenle"),
            ("silme",          "🗑️ Sil"),
        ]
        render_sub_nav(ALT, "nav_ogr_alt")
        alt = st.session_state.get("nav_ogr_alt","excel_yukle")

        # ── Excel Yükle ──
        if alt == "excel_yukle":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>📥 Excel ile Toplu Öğrenci ve Görev Yükle</div>", unsafe_allow_html=True)

            h_okul = kb.get("okul") if (rol!="admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]), key="ex_okul")
            ogrt_hedef = aktif_id
            kb_aktif = kb if not admin_bakis else ayarlar["kullanicilar"].get(admin_bakis_ogrt, kb)

            if rol=="admin" and not admin_bakis:
                ogrt_l = {k:f"{v['ad']} ({v.get('brans','-')})" for k,v in ayarlar["kullanicilar"].items()
                          if v.get("rol")=="ogretmen" and v.get("okul")==h_okul and v.get("onayli",True)}
                ogrt_hedef = st.selectbox("Atanacak Öğretmen", ["admin"]+list(ogrt_l.keys()),
                    format_func=lambda x:"Yönetici" if x=="admin" else ogrt_l[x]) if ogrt_l else "admin"

            c_g1, c_g2, c_g3 = st.columns(3)
            g_tur  = c_g1.selectbox("Görev Türü", ["Proje Ödevi","Ders İçi Performans","1. Performans","2. Performans"])
            g_isim = c_g2.text_input("Görev Adı", placeholder="Dönem Sonu Fen Projesi")
            donem  = c_g3.selectbox("Dönem", ["1. Dönem","2. Dönem"])

            c_dl, c_up = st.columns([1,2])
            c_dl.download_button("📄 Şablon İndir", data=bos_sablon_olustur(), file_name="Ogrenci_Sablon.xlsx")
            uploaded = c_up.file_uploader("Excel Yükle", type=['xlsx'])

            if st.button("🚀 Yükle ve Görevi Ata", use_container_width=True, type="primary"):
                if not uploaded:
                    st.error("Excel dosyası yükleyin!")
                elif not g_isim.strip():
                    st.error("Görev adı girin!")
                else:
                    try:
                        edf = pd.read_excel(uploaded, dtype={"Okul No":str}).fillna("")
                        no_col = next((c for c in edf.columns if "no" in str(c).lower()), edf.columns[0])
                        ad_col = next((c for c in edf.columns if "ad" in str(c).lower()), edf.columns[1])
                        sn_col = next((c for c in edf.columns if "sınıf" in str(c).lower() or "sinif" in str(c).lower()),
                                       edf.columns[2] if len(edf.columns)>2 else None)
                        records = []
                        for _, row in edf.iterrows():
                            o_no = str(row[no_col]).strip().replace('.0','')
                            if not o_no or o_no.lower()=="nan": continue
                            kontrol = df[(df['Okul']==h_okul)&(df['Okul No']==o_no)&
                                          (df['Gorev_Adi']==g_isim.strip())&(df['Atanan_Ogretmen']==ogrt_hedef)]
                            if kontrol.empty:
                                t_ders = (kb_aktif.get("brans","Genel") if ogrt_hedef==aktif_id
                                          else ayarlar["kullanicilar"].get(ogrt_hedef,{}).get("brans","Genel"))
                                records.append({
                                    'okul':h_okul,'ekleyen':aktif_id,'atanan_ogretmen':ogrt_hedef,
                                    'ders':t_ders,'okul_no':o_no,'ogrenci_adi_soyadi':row[ad_col],
                                    'sinif':str(row[sn_col]) if sn_col and str(row[sn_col]).strip()!="" else "Bilinmiyor",
                                    'gorev_turu':g_tur,'gorev_adi':g_isim.strip(),'dinamik_json':{},
                                    'donem':donem,'onaylandi':False
                                })
                        if records:
                            supabase.table('gorevler').insert(records).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(records)} öğrenciye '{g_isim}' görevi tanımlandı!")
                            time.sleep(1); st.rerun()
                        else:
                            st.warning("Geçerli öğrenci bulunamadı veya tümü zaten yüklü.")
                    except Exception as e:
                        st.error(f"Hata: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tekil Ekle ──
        elif alt == "tekil_ekle":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>➕ Tekil Öğrenci / Görev Ekle</div>", unsafe_allow_html=True)
            with st.form("tekil_form"):
                m_okul = kb.get("okul") if (rol!="admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]))
                ogrt_m = aktif_id
                if rol=="admin" and not admin_bakis:
                    ogrt_lm = {k:f"{v['ad']} ({v.get('okul','-')})" for k,v in ayarlar["kullanicilar"].items()
                               if v.get("rol")=="ogretmen" and v.get("onayli",True)}
                    ogrt_m = st.selectbox("Öğretmen", ["admin"]+list(ogrt_lm.keys()),
                        format_func=lambda x:"Yönetici" if x=="admin" else ogrt_lm[x])
                c1m,c2m,c3m = st.columns(3)
                m_no    = c1m.text_input("Okul No")
                m_ad    = c2m.text_input("Ad Soyad")
                m_sinif = c3m.text_input("Sınıf")
                c4m,c5m,c6m = st.columns(3)
                m_gtur  = c4m.selectbox("Görev Türü", ["Proje","Performans"])
                m_gadi  = c5m.text_input("Görev Adı")
                m_donem = c6m.selectbox("Dönem", ["1. Dönem","2. Dönem"])
                if st.form_submit_button("➕ Ekle"):
                    if m_no and m_ad and m_gadi:
                        t_ders = kb.get("brans","") if ogrt_m==aktif_id else ayarlar["kullanicilar"].get(ogrt_m,{}).get("brans","")
                        supabase.table('gorevler').insert({
                            'okul':m_okul,'ekleyen':aktif_id,'atanan_ogretmen':ogrt_m,
                            'ders':t_ders,'okul_no':m_no.strip(),'ogrenci_adi_soyadi':m_ad,
                            'sinif':m_sinif,'gorev_turu':m_gtur,'gorev_adi':m_gadi,
                            'dinamik_json':{},'donem':m_donem,'onaylandi':False
                        }).execute()
                        st.cache_data.clear()
                        st.success("✅ Eklendi!")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("No, ad ve görev adı zorunludur.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Havuzdan Ata ──
        elif alt == "havuz_ata":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>🏫 Havuzdaki Sınıflara Görev Ata</div>", unsafe_allow_html=True)
            st.markdown('<div class="banner info">Okulunuzdaki öğrenciler için kendi dersinizden görev tanımlayabilirsiniz.</div>', unsafe_allow_html=True)

            islem_okul = kb.get("okul") if (rol!="admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]), key="havuz_okul")
            mevcut_siniflar = sorted(df[df['Okul']==islem_okul]['Sınıf'].dropna().unique()) if not df.empty else []

            if mevcut_siniflar:
                secilen = st.multiselect("Görev Atanacak Sınıflar", mevcut_siniflar)
                h_ogrt  = aktif_id
                if rol=="admin" and not admin_bakis:
                    ogrt_lh = {k:f"{v['ad']} ({v.get('brans','-')})" for k,v in ayarlar["kullanicilar"].items()
                               if v.get("rol")=="ogretmen" and v.get("okul")==islem_okul and v.get("onayli",True)}
                    if ogrt_lh:
                        h_ogrt = st.selectbox("Görev Veren", ["admin"]+list(ogrt_lh.keys()),
                            format_func=lambda x:"Yönetici" if x=="admin" else ogrt_lh[x])
                c_h1,c_h2,c_h3 = st.columns(3)
                g_tur_h  = c_h1.selectbox("Görev Türü", ["Proje Ödevi","Performans","1. Performans","2. Performans"], key="gth")
                g_isim_h = c_h2.text_input("Görev Adı", key="gih")
                donem_h  = c_h3.selectbox("Dönem", ["1. Dönem","2. Dönem"], key="dnh")
                if st.button("🚀 Ata", use_container_width=True, type="primary"):
                    if not secilen or not g_isim_h.strip():
                        st.error("Sınıf seçin ve görev adı girin.")
                    else:
                        pool = df[(df['Okul']==islem_okul)&(df['Sınıf'].isin(secilen))].drop_duplicates(subset=['Okul No'])
                        records_h = []
                        for _, row in pool.iterrows():
                            kontrol = df[(df['Okul']==islem_okul)&(df['Okul No']==row['Okul No'])&
                                          (df['Gorev_Adi']==g_isim_h.strip())&(df['Atanan_Ogretmen']==h_ogrt)]
                            if kontrol.empty:
                                t_d = kb.get("brans","Genel") if h_ogrt==aktif_id else ayarlar["kullanicilar"].get(h_ogrt,{}).get("brans","Genel")
                                records_h.append({
                                    'okul':islem_okul,'ekleyen':aktif_id,'atanan_ogretmen':h_ogrt,
                                    'ders':t_d,'okul_no':row['Okul No'],'ogrenci_adi_soyadi':row['Öğrenci Adı Soyadı'],
                                    'sinif':row['Sınıf'],'gorev_turu':g_tur_h,'gorev_adi':g_isim_h.strip(),
                                    'dinamik_json':{},'donem':donem_h,'onaylandi':False
                                })
                        if records_h:
                            supabase.table('gorevler').insert(records_h).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(records_h)} öğrenciye görev atandı!")
                            time.sleep(1); st.rerun()
                        else:
                            st.warning("Görev zaten atanmış.")
            else:
                st.info("Bu okulda öğrenci kaydı yok. Önce Excel ile yükleme yapın.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Geçmişi Düzenle ──
        elif alt == "gecmis_duzenle":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>✏️ Geçmiş Kayıtları Düzenle</div>", unsafe_allow_html=True)

            df_g = df_yetkili[df_yetkili['Gorev_Turu']!='Karne Gorusu']
            if df_g.empty:
                st.warning("Düzenlenecek kayıt yok.")
            else:
                c1e, c2e = st.columns(2)
                gorevler = sorted(df_g['Gorev_Adi'].dropna().unique())
                sec_gorev = c1e.selectbox("Görev", ["— Seçiniz —"]+gorevler)
                if sec_gorev != "— Seçiniz —":
                    df_sg = df_g[df_g['Gorev_Adi']==sec_gorev]
                    filtre_d = c2e.radio("Filtre", ["Tümü","Sadece Değerlendirilenler"], horizontal=True)
                    if filtre_d == "Sadece Değerlendirilenler":
                        df_sg = df_sg[pd.to_numeric(df_sg['Toplam Puan'], errors='coerce') > 0]

                    ogr_l = df_sg.apply(lambda r: f"{r['Okul No']} — {r['Öğrenci Adı Soyadı']}", axis=1).tolist()
                    sec_ogr = st.selectbox("Öğrenci", ["— Seçiniz —"]+ogr_l)

                    if sec_ogr != "— Seçiniz —":
                        o_no = sec_ogr.split(" — ")[0].strip()
                        satir = df_sg[df_sg['Okul No']==o_no].iloc[0]
                        aktif_sablon = ayarlar["sablonlar"].get(SABLON_ADI, CEKIRDEK_SABLON)
                        eski_json = {}
                        try:
                            if pd.notna(satir.get('Dinamik_JSON','')):
                                eski_json = json.loads(str(satir['Dinamik_JSON']))
                        except: pass

                        st.markdown(f'<div class="banner info">Düzenleniyor: <strong>{sec_ogr}</strong> | Mevcut Puan: <strong>{satir.get("Toplam Puan",0)}</strong></div>', unsafe_allow_html=True)

                        # AI Modu
                        st.markdown("#### 🤖 Yapay Zeka ile Yeniden Değerlendir")
                        ai_mod_e = st.radio("Mod", ["A","B","C"], format_func=lambda x:{
                            "A":"📝 Mod A — Yeni Yorum Gir, AI Puanlasın",
                            "B":"🎯 Mod B — Hedef Puan, AI Dağıtsın",
                            "C":"✋ Mod C — Puanları Koru, AI Açıklasın"
                        }[x], horizontal=True, key="ai_rad_e")
                        ham_e, hedef_e = "", int(satir.get('Toplam Puan',85) or 85)
                        if ai_mod_e == "A":
                            ham_e = st.text_area("Öğretmen Notu:", key="ham_e_txt")
                        elif ai_mod_e == "B":
                            hedef_e = st.slider("Hedef Puan", 0, 100, hedef_e, key="hedef_e_sl")

                        if st.button("✨ AI Yeniden Değerlendir", use_container_width=True, key="ai_btn_e"):
                            with st.spinner("AI analiz ediyor..."):
                                try:
                                    mp = {k['id']: int(eski_json.get(f"{k['id']}_puan",0)) for k in aktif_sablon}
                                    res = ai_degerlendirme_yap(satir.to_dict(), aktif_sablon, ai_mod_e,
                                                                ham_e, hedef_e, mp, kb.get("ad",""), satir['Ders'])
                                    for k in aktif_sablon:
                                        if k['id'] in res.get("puanlar",{}):
                                            st.session_state[f"edit_vp_{k['id']}"] = int(res["puanlar"][k['id']])
                                        if k['id'] in res.get("aciklamalar",{}):
                                            st.session_state[f"edit_va_{k['id']}"] = res["aciklamalar"][k['id']]
                                    if "genel" in res:
                                        st.session_state["edit_vg"] = res["genel"]
                                    st.success("✅ Hazır! Formu kontrol edip kaydedin.")
                                except Exception as e:
                                    st.error(f"AI hatası: {e}")

                        st.markdown("#### 📝 Düzenleme Formu")
                        with st.form("edit_form"):
                            toplam_e = 0
                            gunceller = {}
                            for k in aktif_sablon:
                                def_p = st.session_state.get(f"edit_vp_{k['id']}", int(eski_json.get(f"{k['id']}_puan",0)))
                                def_a = st.session_state.get(f"edit_va_{k['id']}", str(eski_json.get(f"{k['id']}_aciklama","")))
                                cc1, cc2 = st.columns([1,3])
                                pv = cc1.number_input(f"{k['baslik']} (Max:{k['max']})", 0, k['max'], def_p)
                                av = cc2.text_input(f"Açıklama — {k['baslik']}", def_a)
                                toplam_e += pv
                                gunceller[f"{k['id']}_puan"] = pv
                                gunceller[f"{k['id']}_aciklama"] = av
                            gv_e = st.text_area("💬 Genel Yorum", st.session_state.get("edit_vg", str(satir.get('Genel Değerlendirme Yorumu',''))))
                            st.info(f"Yeni Toplam: **{toplam_e} / 100**")
                            if st.form_submit_button("💾 Güncelle ve Kaydet"):
                                supabase.table('gorevler').update({
                                    'dinamik_json': gunceller,
                                    'genel_degerlendirme_yorumu': gv_e,
                                    'toplam_puan': toplam_e
                                }).eq('okul_no', o_no).eq('gorev_adi', sec_gorev).execute()
                                st.cache_data.clear()
                                st.success("✅ Güncellendi!")
                                time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Silme ──
        elif alt == "silme":
            st.markdown('<div class="banner warn">⚠️ Silme işlemleri geri alınamaz! Önce Raporlar → Yedekleme bölümünden yedek alın.</div>', unsafe_allow_html=True)
            SIL_ALT = [("tekil_sil","📌 Tekil"),("sinif_sil","🏫 Sınıf Toplu"),("okul_sil","🏢 Okul Toplu")]
            render_sub_nav(SIL_ALT, "nav_sil_alt")
            sil_alt = st.session_state.get("nav_sil_alt","tekil_sil")

            st.markdown('<div class="card">', unsafe_allow_html=True)
            if sil_alt == "tekil_sil":
                if not df_yetkili.empty:
                    s_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} — {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                    silinecek = st.selectbox("Silinecek Kayıt", ["— Seçiniz —"]+s_liste)
                    if st.button("🗑️ Sil", type="primary") and silinecek != "— Seçiniz —":
                        o_no = silinecek.split(" — ")[0].strip()
                        g_ad = silinecek.split(" | ")[1].strip()
                        supabase.table('gorevler').delete().eq('okul_no',o_no).eq('gorev_adi',g_ad).execute()
                        st.cache_data.clear()
                        st.success("Silindi.")
                        time.sleep(1); st.rerun()
                else:
                    st.info("Kayıt yok.")

            elif sil_alt == "sinif_sil":
                sil_okul2 = kb.get("okul") if (rol!="admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]), key="sil_okul2")
                siniflar_s = sorted(df[df['Okul']==sil_okul2]['Sınıf'].dropna().unique()) if not df.empty else []
                if siniflar_s:
                    sec_sinif_s = st.multiselect("Silinecek Sınıflar", siniflar_s)
                    sec_gorev_s = st.selectbox("Filtre (Opsiyonel)", ["Tüm Görevler"]+sorted(df[df['Okul']==sil_okul2]['Gorev_Adi'].dropna().unique()))
                    if sec_sinif_s:
                        kac = len(df[(df['Okul']==sil_okul2)&(df['Sınıf'].isin(sec_sinif_s))])
                        st.warning(f"{kac} kayıt silinecek!")
                        if st.checkbox(f"Evet, {kac} kaydı silmek istiyorum.") and st.button("🗑️ Sil", type="primary", key="sinif_sil_btn"):
                            q = supabase.table('gorevler').delete().eq('okul',sil_okul2).in_('sinif',sec_sinif_s)
                            if sec_gorev_s != "Tüm Görevler":
                                q = supabase.table('gorevler').delete().eq('okul',sil_okul2).in_('sinif',sec_sinif_s).eq('gorev_adi',sec_gorev_s)
                            q.execute()
                            st.cache_data.clear()
                            st.success("Silindi.")
                            time.sleep(1); st.rerun()

            elif sil_alt == "okul_sil":
                if rol != "admin":
                    st.error("Sadece yönetici yapabilir.")
                else:
                    sil_okul3 = st.selectbox("Tümü Silinecek Okul", sorted(ayarlar["okullar"]))
                    kac3 = len(df[df['Okul']==sil_okul3]) if not df.empty else 0
                    if kac3>0:
                        st.error(f"⛔ {kac3} kayıt silinecek!")
                        if st.checkbox(f"Evet, {sil_okul3} okulunun tüm verisini sil") and st.button("⛔ Sil", type="primary", key="okul_sil_btn"):
                            supabase.table('gorevler').delete().eq('okul',sil_okul3).execute()
                            st.cache_data.clear()
                            st.success("Silindi.")
                            time.sleep(1); st.rerun()
                    else:
                        st.info("Bu okulda kayıt yok.")
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: AI DEĞERLENDİRME
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ai_degerlendirme":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='card-baslik'>🤖 Yapay Zeka Destekli Puanlama</div>", unsafe_allow_html=True)

        df_g = df_yetkili[df_yetkili['Gorev_Turu']!='Karne Gorusu']
        if df_g.empty:
            st.warning("Değerlendirilecek görev bulunamadı.")
        else:
            c1ai, c2ai = st.columns([2,1])
            gorev_liste = df_g.apply(lambda r: f"{r['Okul No']} — {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
            sec_gorev  = c1ai.selectbox("🎯 Öğrenci ve Görev", ["— Seçiniz —"]+gorev_liste)
            s_isimler  = list(ayarlar.get("sablonlar",{}).keys())
            sec_sablon = c2ai.selectbox("📋 Şablon", s_isimler)
            aktif_sab  = ayarlar["sablonlar"].get(sec_sablon, CEKIRDEK_SABLON)

            if sec_gorev != "— Seçiniz —":
                o_no = sec_gorev.split(" — ")[0].strip()
                g_ad = sec_gorev.split(" | ")[1].strip()
                idx_l = df[(df['Okul No']==o_no)&(df['Gorev_Adi']==g_ad)].index
                if len(idx_l) == 0:
                    st.error("Kayıt bulunamadı.")
                else:
                    idx  = idx_l[0]
                    bilgi = df.iloc[idx]

                    if st.session_state.get("aktif_idx") != idx:
                        st.session_state["aktif_idx"] = idx
                        e_p = {}
                        try:
                            if pd.notna(bilgi.get('Dinamik_JSON','')):
                                e_p = json.loads(str(bilgi['Dinamik_JSON']))
                        except: pass
                        for k in aktif_sab:
                            st.session_state[f"vp_{k['id']}"] = int(e_p.get(f"{k['id']}_puan",0))
                            st.session_state[f"va_{k['id']}"] = str(e_p.get(f"{k['id']}_aciklama",""))
                        st.session_state["vg"] = str(bilgi.get('Genel Değerlendirme Yorumu',""))

                    st.markdown(f"""
                    <div class="banner info">
                        <strong>{bilgi.get('Öğrenci Adı Soyadı','')}</strong> &nbsp;·&nbsp;
                        {bilgi.get('Sınıf','')} &nbsp;·&nbsp;
                        {bilgi.get('Gorev_Adi','')} &nbsp;·&nbsp;
                        No: {bilgi.get('Okul No','')}
                    </div>""", unsafe_allow_html=True)

                    ai_modu = st.radio("🤖 AI Modu", ["A","B","C"], format_func=lambda x:{
                        "A":"📝 Mod A — Yorum Gir, AI Puanlasın",
                        "B":"🎯 Mod B — Hedef Puan Ver, AI Dağıtsın",
                        "C":"✋ Mod C — Manuel Puan, AI Açıklasın"
                    }[x], horizontal=True, label_visibility="collapsed")

                    ham, hedef = "", 85
                    if ai_modu == "A":
                        ham = st.text_area("Öğretmen notunuz:", placeholder="Öğrenci projeyi zamanında teslim etti...")
                    elif ai_modu == "B":
                        hedef = st.slider("Hedef Puan", 0, 100, 85)

                    if st.button("✨ Yapay Zekayı Çalıştır", use_container_width=True, type="primary"):
                        with st.spinner("AI isme özel değerlendiriyor..."):
                            try:
                                mp = {k['id']: st.session_state.get(f"vp_{k['id']}",0) for k in aktif_sab}
                                res = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sab, ai_modu,
                                                           ham, hedef, mp, kb.get("ad",""), bilgi['Ders'])
                                for k in aktif_sab:
                                    if k['id'] in res.get("puanlar",{}):
                                        st.session_state[f"vp_{k['id']}"] = int(res["puanlar"][k['id']])
                                    if k['id'] in res.get("aciklamalar",{}):
                                        st.session_state[f"va_{k['id']}"] = res["aciklamalar"][k['id']]
                                if "genel" in res:
                                    st.session_state["vg"] = res["genel"]
                                st.success("✅ Değerlendirme hazır! Kontrol edip kaydedin.")
                            except Exception as e:
                                st.error(f"AI hatası: {e}")

                    st.markdown("#### 📝 Puanlama Formu")
                    with st.form("kayit_form"):
                        toplam_ai = 0
                        for k in aktif_sab:
                            st.markdown(f"""
                            <div class="kriter-card">
                              <div class="k-baslik">{k.get('icon','📌')} {k['baslik']}
                                <span style="color:#94a3b8;font-weight:400;font-size:0.78rem"> (Max: {k['max']})</span></div>
                              <div class="k-acik">{k['aciklama']}</div>
                            </div>""", unsafe_allow_html=True)
                            c1k, c2k = st.columns([1,3])
                            pv = c1k.number_input(f"Puan", 0, k['max'], key=f"vp_{k['id']}", label_visibility="collapsed")
                            av = c2k.text_area("Açıklama", key=f"va_{k['id']}", height=65, label_visibility="collapsed")
                            toplam_ai += pv
                        gv = st.text_area("💬 Genel Yorum", key="vg", height=85)
                        st.markdown(f"""<div class="banner ok" style="font-size:1.05rem;font-weight:800;">
                            Toplam: <span style="color:#059669">{toplam_ai} / 100</span></div>""", unsafe_allow_html=True)
                        if st.form_submit_button("💾 Kaydet", use_container_width=True):
                            flat = {}
                            for k in aktif_sab:
                                flat[f"{k['id']}_puan"] = st.session_state[f"vp_{k['id']}"]
                                flat[f"{k['id']}_aciklama"] = st.session_state[f"va_{k['id']}"]
                            supabase.table('gorevler').update({
                                'dinamik_json': flat,
                                'genel_degerlendirme_yorumu': gv,
                                'toplam_puan': toplam_ai
                            }).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                            st.cache_data.clear()
                            st.success("✅ Kaydedildi!")
                            time.sleep(1); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: RAPORLAR
    # ══════════════════════════════════════════════════
    elif aktif_ana == "raporlar":
        RAP_ALT = [("sinif_rapor","📊 Sınıf Raporları"),("yedekleme","💾 Yedekleme")]
        render_sub_nav(RAP_ALT, "nav_rapor_alt")
        alt_r = st.session_state.get("nav_rapor_alt","sinif_rapor")

        if alt_r == "sinif_rapor":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>📊 Sınıf Raporları</div>", unsafe_allow_html=True)

            df_rp = df_yetkili[df_yetkili['Gorev_Turu']!='Karne Gorusu']
            if not df_rp.empty:
                c1r,c2r,c3r = st.columns(3)
                donem_r = c1r.selectbox("Dönem", ["Tümü","1. Dönem","2. Dönem"])
                sinif_r = c2r.selectbox("Sınıf", ["Tümü"]+sorted(df_rp['Sınıf'].dropna().unique()))
                gorev_r = c3r.selectbox("Görev", ["Tümü"]+sorted(df_rp['Gorev_Adi'].dropna().unique()))

                df_r = df_rp.copy()
                if donem_r != "Tümü" and 'Donem' in df_r.columns:
                    df_r = df_r[df_r['Donem']==donem_r]
                if sinif_r != "Tümü":
                    df_r = df_r[df_r['Sınıf']==sinif_r]
                if gorev_r != "Tümü":
                    df_r = df_r[df_r['Gorev_Adi']==gorev_r]

                if not df_r.empty:
                    df_rc = df_r.copy()
                    df_rc['Toplam Puan'] = pd.to_numeric(df_rc['Toplam Puan'], errors='coerce').fillna(0)
                    ort = round(df_rc['Toplam Puan'].mean(), 1)

                    st.markdown(f"""<div class="stat-grid">
                        <div class="stat-box"><div class="stat-num">{len(df_rc)}</div><div class="stat-lbl">Toplam Kayıt</div></div>
                        <div class="stat-box g"><div class="stat-num">{ort}</div><div class="stat-lbl">Ortalama</div></div>
                        <div class="stat-box o"><div class="stat-num">{int(df_rc['Toplam Puan'].max())}</div><div class="stat-lbl">En Yüksek</div></div>
                        <div class="stat-box r"><div class="stat-num">{len(df_rc[df_rc['Toplam Puan']==0])}</div><div class="stat-lbl">Değerlendirilmemiş</div></div>
                    </div>""", unsafe_allow_html=True)

                    st.dataframe(
                        df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Adi','Toplam Puan']].sort_values('Toplam Puan',ascending=False),
                        use_container_width=True, hide_index=True
                    )

                    c_b1, c_b2, c_b3 = st.columns(3)
                    out_xls = io.BytesIO()
                    with pd.ExcelWriter(out_xls, engine='xlsxwriter') as w:
                        df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Adi','Toplam Puan']].to_excel(w, index=False)
                    c_b1.download_button("📊 Excel", data=out_xls.getvalue(), file_name=f"{sinif_r}_Cizelge.xlsx", use_container_width=True)

                    if c_b2.button("🖨️ Kişisel Karneler", use_container_width=True):
                        s_aktif = ayarlar["sablonlar"].get(list(ayarlar["sablonlar"].keys())[0], CEKIRDEK_SABLON)
                        h = toplu_karne_html(df_r, kb.get("ad",""), kb.get("brans",""), s_aktif)
                        st.download_button("📥 HTML İndir", data=h, file_name=f"{sinif_r}_Karneler.html", mime="text/html", use_container_width=True)

                    if c_b3.button("📈 Analiz Raporu", use_container_width=True):
                        analiz = sinif_analiz_html(df_r, sinif_r, kb.get("ad",""))
                        st.download_button("📥 Analiz İndir", data=analiz, file_name=f"{sinif_r}_Analiz.html", mime="text/html", use_container_width=True)
                else:
                    st.info("Filtreye uyan kayıt bulunamadı.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif alt_r == "yedekleme":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>💾 Veri Yedekleme</div>", unsafe_allow_html=True)
            c1y, c2y = st.columns(2)
            out_y = io.BytesIO()
            with pd.ExcelWriter(out_y, engine='xlsxwriter') as w:
                df_yetkili.to_excel(w, index=False)
            c1y.download_button("📥 Kendi Verilerimi Yedekle", data=out_y.getvalue(),
                                 file_name=f"Yedek_{time.strftime('%Y%m%d_%H%M')}.xlsx", use_container_width=True)
            if rol == "admin":
                out_t = io.BytesIO()
                with pd.ExcelWriter(out_t, engine='xlsxwriter') as w:
                    df.to_excel(w, index=False)
                c2y.download_button("📥 Tüm Sistemi Yedekle", data=out_t.getvalue(),
                                    file_name=f"SistemYedek_{time.strftime('%Y%m%d_%H%M')}.xlsx", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: KARNE GÖRÜŞLERİ — TAM YENİLENDİ
    # ══════════════════════════════════════════════════
    elif aktif_ana == "karne":
        KARNE_ALT = [
            ("yukle",   "📥 Liste Yükle"),
            ("liste",   "📋 Öğrenci Listesi"),
            ("arsiv",   "🗂️ Dönem Arşivi"),
        ]
        render_sub_nav(KARNE_ALT, "nav_karne_alt")
        k_alt = st.session_state.get("nav_karne_alt","liste")

        # ── Karne: Liste Yükle ──
        if k_alt == "yukle":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>📥 Öğrenci Not Listesi Yükle</div>", unsafe_allow_html=True)
            st.markdown('<div class="banner info">Excel dosyasında "Öğrenci No", "Adı Soyadı", "Sınıfı" ve ders notları + "Davranış" sütunu olmalıdır. Davranış 0-100 arası bir sayı girin.</div>', unsafe_allow_html=True)

            c_dk1, c_dk2 = st.columns([1,2])
            c_dk1.download_button("📄 Örnek Şablon İndir", data=eokul_sablon_olustur(), file_name="Karne_Sablon.xlsx")
            k_dosya = c_dk2.file_uploader("Not Listesini Yükle", type=['xlsx','csv','xls'])
            k_donem = st.selectbox("Bu Listeyi Hangi Döneme Ait Kaydedeceğiz?", ["1. Dönem","2. Dönem"])

            if k_dosya and st.button("🚀 Listeyi Karne Arşivine Aktar", type="primary", use_container_width=True):
                try:
                    kdf = pd.read_csv(k_dosya, sep=None, engine='python') if k_dosya.name.endswith('.csv') else pd.read_excel(k_dosya)
                    kdf = kdf.fillna("")
                    cols = kdf.columns.tolist()
                    no_col    = next((c for c in cols if "no" in str(c).lower()), cols[0])
                    ad_col    = next((c for c in cols if "ad" in str(c).lower()), cols[1] if len(cols)>1 else cols[0])
                    sinif_col = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols)>2 else None)
                    not_cols  = [c for c in cols if c not in [no_col, ad_col, sinif_col]]

                    records_k = []
                    for _, row in kdf.iterrows():
                        o_no = str(row[no_col]).strip().replace('.0','')
                        if not o_no or o_no.lower()=="nan" or o_no=="": continue
                        notlar_d = {d: str(row[d]) for d in not_cols if str(row[d]).strip() not in ["","nan","0.0"]}
                        kontrol  = df[(df['Okul']==kb.get("okul"))&(df['Okul No']==o_no)&
                                       (df['Gorev_Turu']=='Karne Gorusu')&(df.get('Donem',pd.Series(['']))==k_donem)]
                        if kontrol.empty:
                            records_k.append({
                                'okul':kb.get("okul"),'ekleyen':aktif_id,'atanan_ogretmen':aktif_id,
                                'ders':'Karne','okul_no':o_no,'ogrenci_adi_soyadi':row[ad_col],
                                'sinif':str(row[sinif_col]) if sinif_col and str(row[sinif_col]).strip() not in ["","nan"] else "Bilinmiyor",
                                'gorev_turu':'Karne Gorusu',
                                'gorev_adi':f"{k_donem} Karne Görüşü",
                                'dinamik_json':{"notlar":notlar_d},
                                'genel_degerlendirme_yorumu':"",
                                'donem':k_donem,'onaylandi':False
                            })
                    if records_k:
                        supabase.table('gorevler').insert(records_k).execute()
                        st.cache_data.clear()
                        st.success(f"✅ {len(records_k)} öğrenci arşive eklendi! 'Öğrenci Listesi' sekmesinden işlem yapabilirsiniz.")
                        st.session_state["nav_karne_alt"] = "liste"
                        time.sleep(2); st.rerun()
                    else:
                        st.warning("Bu dönem için öğrenciler zaten arşivde.")
                except Exception as e:
                    st.error(f"Hata: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Karne: Öğrenci Listesi (Ana İş Ekranı) ──
        elif k_alt == "liste":
            df_karne = df_yetkili[df_yetkili['Gorev_Turu']=='Karne Gorusu'].copy()

            if df_karne.empty:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="banner warn">📋 Henüz karne listesi yüklenmemiş. "Liste Yükle" sekmesinden başlayın.</div>', unsafe_allow_html=True)
                if st.button("📥 Liste Yükle Sayfasına Git", type="primary"):
                    st.session_state["nav_karne_alt"] = "yukle"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Filtreler
                c_f1, c_f2, c_f3, c_f4 = st.columns(4)
                donem_k   = c_f1.selectbox("Dönem", ["Tümü","1. Dönem","2. Dönem"], key="karne_donem")
                sinif_k   = c_f2.selectbox("Sınıf", ["Tümü"]+sorted(df_karne['Sınıf'].dropna().unique()), key="karne_sinif")
                durum_k   = c_f3.selectbox("Durum", ["Tümü","Görüş Yazıldı","Görüş Yok","Onaylananlar"], key="karne_durum")
                arama_k   = c_f4.text_input("🔍 İsim Ara", key="karne_arama")

                df_kf = df_karne.copy()
                if donem_k != "Tümü" and 'Donem' in df_kf.columns:
                    df_kf = df_kf[df_kf['Donem']==donem_k]
                if sinif_k != "Tümü":
                    df_kf = df_kf[df_kf['Sınıf']==sinif_k]
                if durum_k == "Görüş Yazıldı":
                    df_kf = df_kf[df_kf['Genel Değerlendirme Yorumu'].notna() & (df_kf['Genel Değerlendirme Yorumu']!="")]
                elif durum_k == "Görüş Yok":
                    df_kf = df_kf[df_kf['Genel Değerlendirme Yorumu'].isna() | (df_kf['Genel Değerlendirme Yorumu']=="")]
                elif durum_k == "Onaylananlar":
                    df_kf = df_kf[df_kf['Onaylandi']==True]
                if arama_k:
                    df_kf = df_kf[df_kf['Öğrenci Adı Soyadı'].str.contains(arama_k, case=False, na=False)]

                # Özet istatistikler
                toplam_k = len(df_kf)
                yazilan  = len(df_kf[df_kf['Genel Değerlendirme Yorumu'].notna() & (df_kf['Genel Değerlendirme Yorumu']!="")])
                onaylanan = len(df_kf[df_kf.get('Onaylandi',pd.Series([False]*len(df_kf)))==True]) if 'Onaylandi' in df_kf.columns else 0
                bekleyen  = toplam_k - yazilan

                st.markdown(f"""<div class="stat-grid">
                    <div class="stat-box"><div class="stat-num">{toplam_k}</div><div class="stat-lbl">Toplam Öğrenci</div></div>
                    <div class="stat-box g"><div class="stat-num">{yazilan}</div><div class="stat-lbl">Görüş Yazıldı</div></div>
                    <div class="stat-box p"><div class="stat-num">{onaylanan}</div><div class="stat-lbl">Onaylandı</div></div>
                    <div class="stat-box r"><div class="stat-num">{bekleyen}</div><div class="stat-lbl">Bekleniyor</div></div>
                </div>""", unsafe_allow_html=True)

                # Toplu AI Butonu
                yazilmamis = df_kf[df_kf['Genel Değerlendirme Yorumu'].isna() | (df_kf['Genel Değerlendirme Yorumu']=="")]
                if not yazilmamis.empty:
                    with st.expander(f"⚡ Toplu AI Görüş Üret ({len(yazilmamis)} öğrenci için)", expanded=False):
                        st.markdown('<div class="banner warn">⚠️ Bu işlem tüm görüş yazılmamış öğrenciler için AI görüşü üretir. Sonra tek tek düzenleyebilirsiniz.</div>', unsafe_allow_html=True)
                        if st.button("🤖 Tüm Sınıf İçin Toplu Görüş Üret", type="primary", use_container_width=True, key="toplu_ai_btn"):
                            progress_bar = st.progress(0)
                            status_txt   = st.empty()
                            basarili, hata = 0, 0
                            toplam_count = len(yazilmamis)
                            for i, (_, satir_k) in enumerate(yazilmamis.iterrows()):
                                status_txt.text(f"İşleniyor: {satir_k['Öğrenci Adı Soyadı']} ({i+1}/{toplam_count})")
                                progress_bar.progress((i+1)/toplam_count)
                                try:
                                    notlar = {}
                                    davranis = 75
                                    try:
                                        djson = json.loads(str(satir_k.get('Dinamik_JSON','{}')))
                                        notlar = djson.get('notlar',{})
                                        davranis = int(float(str(notlar.get('Davranış', 75) or 75)))
                                    except: pass
                                    yeni_g = ai_karne_gorusu_yaz(
                                        satir_k['Öğrenci Adı Soyadı'],
                                        satir_k['Sınıf'],
                                        {k:v for k,v in notlar.items() if k!='Davranış'},
                                        davranis, "", kb.get("ad","")
                                    )
                                    supabase.table('gorevler').update({
                                        'genel_degerlendirme_yorumu': yeni_g,
                                        'onaylandi': False
                                    }).eq('okul_no', satir_k['Okul No']).eq('gorev_turu','Karne Gorusu').eq('donem', satir_k.get('Donem','1. Dönem')).execute()
                                    basarili += 1
                                    time.sleep(0.5)
                                except Exception as e:
                                    hata += 1
                            st.cache_data.clear()
                            st.success(f"✅ {basarili} görüş üretildi. {hata} hata.")
                            time.sleep(1); st.rerun()

                # Öğrenci Listesi
                st.markdown("---")
                for _, satir_k in df_kf.iterrows():
                    yorum = satir_k.get('Genel Değerlendirme Yorumu','')
                    onayli = satir_k.get('Onaylandi', False)
                    notlar, davranis = {}, 75
                    try:
                        djson = json.loads(str(satir_k.get('Dinamik_JSON','{}')))
                        notlar = djson.get('notlar',{})
                        davranis = int(float(str(notlar.get('Davranış', 75) or 75)))
                    except: pass

                    durum_cls = "rozet-onay" if onayli else ("rozet-bekle" if yorum else "rozet-yok")
                    durum_txt = "✅ Onaylandı" if onayli else ("📝 Görüş Var" if yorum else "⏳ Bekleniyor")
                    dav_renk  = "#10b981" if davranis>=85 else ("#f59e0b" if davranis>=65 else "#ef4444")

                    col_k1, col_k2 = st.columns([4,1])
                    with col_k1:
                        st.markdown(f"""
                        <div class="karne-preview {'onaylandi' if onayli else 'bekliyor' if yorum else ''}">
                            <div class="karne-onay-rozet {durum_cls}">{durum_txt}</div>
                            <div class="karne-ogrenci">{satir_k['Öğrenci Adı Soyadı']}</div>
                            <div class="karne-detay">
                                {satir_k.get('Sınıf','')} · No: {satir_k.get('Okul No','')} ·
                                <span class="donem-chip donem-{'1' if '1' in str(satir_k.get('Donem','')) else '2'}">{satir_k.get('Donem','')}</span>
                            </div>
                            <div style="margin-top:8px;">
                                <span style="font-size:0.78rem;color:{dav_renk};font-weight:700;">
                                    Davranış: {davranis}/100
                                </span>
                                <div class="davranis-bar" style="width:200px;margin-top:3px;">
                                    <div class="davranis-fill" style="width:{davranis}%;background:{dav_renk};"></div>
                                </div>
                            </div>
                            {f'<div class="karne-yorum">{yorum[:200]}{"..." if len(yorum or "")>200 else ""}</div>' if yorum else '<div style="color:#94a3b8;font-size:0.82rem;margin-top:8px;font-style:italic;">Görüş henüz yazılmamış</div>'}
                        </div>""", unsafe_allow_html=True)

                    with col_k2:
                        o_no_k  = satir_k['Okul No']
                        donem_k_val = satir_k.get('Donem','1. Dönem')
                        btn_key = f"karne_edit_{o_no_k}_{donem_k_val}"

                        if st.button("✏️ Düzenle", key=btn_key, use_container_width=True, type="primary"):
                            st.session_state["karne_sec_no"]    = o_no_k
                            st.session_state["karne_sec_donem"] = donem_k_val
                            st.session_state["karne_panel"]     = True
                            st.rerun()

                # ── Düzenleme Paneli (Modal Benzeri) ──
                if st.session_state.get("karne_panel") and st.session_state.get("karne_sec_no"):
                    o_no_panel = st.session_state["karne_sec_no"]
                    d_panel    = st.session_state.get("karne_sec_donem","1. Dönem")
                    df_panel   = df_karne[(df_karne['Okul No']==o_no_panel)]
                    if 'Donem' in df_panel.columns:
                        df_panel = df_panel[df_panel['Donem']==d_panel]

                    if not df_panel.empty:
                        satir_p = df_panel.iloc[0]
                        notlar_p, davranis_p = {}, 75
                        try:
                            djson_p = json.loads(str(satir_p.get('Dinamik_JSON','{}')))
                            notlar_p  = djson_p.get('notlar',{})
                            davranis_p = int(float(str(notlar_p.get('Davranış',75) or 75)))
                        except: pass

                        st.markdown("---")
                        st.markdown(f'<div class="card">', unsafe_allow_html=True)
                        st.markdown(f"<div class='card-baslik'>✏️ Karne Görüşü Düzenle — {satir_p['Öğrenci Adı Soyadı']}</div>", unsafe_allow_html=True)

                        # Not Profili
                        if notlar_p:
                            not_html_p = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;'>"
                            for ders, n in notlar_p.items():
                                if str(n).strip() not in ["","nan"] and ders != "Davranış":
                                    try:
                                        n_int = int(float(str(n)))
                                        renk = "#dcfce7" if n_int>=85 else ("#fef9c3" if n_int>=65 else "#fee2e2")
                                        renk_t = "#065f46" if n_int>=85 else ("#854d0e" if n_int>=65 else "#991b1b")
                                        not_html_p += f"<div style='background:{renk};color:{renk_t};padding:5px 10px;border-radius:7px;font-size:0.82rem;font-weight:700;'>{ders}: {n_int}</div>"
                                    except: pass
                            not_html_p += "</div>"
                            st.markdown(not_html_p, unsafe_allow_html=True)

                        # Davranış göstergesi
                        dav_r = "#10b981" if davranis_p>=85 else ("#f59e0b" if davranis_p>=65 else "#ef4444")
                        st.markdown(f"""
                        <div style="margin-bottom:16px;">
                            <div style="font-size:0.82rem;font-weight:700;color:#64748b;margin-bottom:6px;display:flex;justify-content:space-between;">
                                <span>Davranış Notu</span>
                                <span style="color:{dav_r};font-weight:800;">{davranis_p}/100</span>
                            </div>
                            <div class="davranis-bar">
                                <div class="davranis-fill" style="width:{davranis_p}%;background:{dav_r};"></div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                        # AI Üretme
                        c_ai1, c_ai2 = st.columns([2,1])
                        gozlem_p = c_ai1.text_area("Ek Gözlem (Opsiyonel)", key="gozlem_panel",
                                                    placeholder="Örn: Bu dönem derslere katılımı arttı, çok gayret etti...")
                        if c_ai2.button("✨ AI Görüş Üret", type="primary", use_container_width=True, key="ai_karne_panel"):
                            with st.spinner("AI görüş yazıyor..."):
                                try:
                                    g_metin = ai_karne_gorusu_yaz(
                                        satir_p['Öğrenci Adı Soyadı'],
                                        satir_p['Sınıf'],
                                        {k:v for k,v in notlar_p.items() if k!='Davranış'},
                                        davranis_p, gozlem_p, kb["ad"]
                                    )
                                    st.session_state["karne_ai_yorum"] = g_metin
                                    st.success("✅ Görüş üretildi! Aşağıdan düzenleyip onaylayın.")
                                except Exception as e:
                                    st.error(f"AI hatası: {e}")

                        # Yorum düzenleme + Önizleme
                        mevcut_yorum = st.session_state.get("karne_ai_yorum",
                                        satir_p.get('Genel Değerlendirme Yorumu',''))
                        yorum_edit = st.text_area("📝 Karne Görüşü (Düzenle / Onayla)",
                                                   value=mevcut_yorum, height=140, key="yorum_panel_txt")

                        # Önizleme
                        if yorum_edit:
                            with st.expander("👁️ Karne Önizlemesi (Tıkla)", expanded=False):
                                oniz_html = karne_onizleme_html(
                                    satir_p['Öğrenci Adı Soyadı'],
                                    satir_p.get('Sınıf',''),
                                    satir_p.get('Okul No',''),
                                    d_panel, davranis_p, yorum_edit,
                                    {k:v for k,v in notlar_p.items() if k!='Davranış'}
                                )
                                st.components.v1.html(oniz_html, height=500, scrolling=True)
                                st.download_button("📥 Bu Karneyi PDF/HTML Olarak İndir",
                                                   data=oniz_html,
                                                   file_name=f"{satir_p['Öğrenci Adı Soyadı']}_Karne.html",
                                                   mime="text/html", use_container_width=True)

                        # Onaylama ve Kayıt Butonları
                        c_s1, c_s2, c_s3 = st.columns(3)
                        if c_s1.button("💾 Kaydet (Onaysız)", use_container_width=True, key="karne_kaydet_btn"):
                            supabase.table('gorevler').update({
                                'genel_degerlendirme_yorumu': yorum_edit,
                                'onaylandi': False
                            }).eq('okul_no', o_no_panel).eq('gorev_turu','Karne Gorusu').execute()
                            st.cache_data.clear()
                            st.session_state.pop("karne_ai_yorum", None)
                            st.session_state["karne_panel"] = False
                            st.success("Kaydedildi.")
                            time.sleep(1); st.rerun()

                        if c_s2.button("✅ Onayla ve Kaydet", use_container_width=True, type="primary", key="karne_onayla_btn"):
                            supabase.table('gorevler').update({
                                'genel_degerlendirme_yorumu': yorum_edit,
                                'onaylandi': True
                            }).eq('okul_no', o_no_panel).eq('gorev_turu','Karne Gorusu').execute()
                            st.cache_data.clear()
                            st.session_state.pop("karne_ai_yorum", None)
                            st.session_state["karne_panel"] = False
                            st.success("✅ Onaylandı ve kaydedildi!")
                            time.sleep(1); st.rerun()

                        if c_s3.button("❌ İptal", use_container_width=True, key="karne_iptal_btn"):
                            st.session_state.pop("karne_ai_yorum", None)
                            st.session_state["karne_panel"] = False
                            st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)

        # ── Karne: Dönem Arşivi ──
        elif k_alt == "arsiv":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<div class='card-baslik'>🗂️ Dönem Arşivi</div>", unsafe_allow_html=True)

            df_arsiv = df_yetkili[df_yetkili['Gorev_Turu']=='Karne Gorusu'].copy()
            if df_arsiv.empty:
                st.info("Arşivde kayıt yok.")
            else:
                c_a1, c_a2 = st.columns(2)
                donem_a = c_a1.selectbox("Dönem", ["Tümü","1. Dönem","2. Dönem"], key="arsiv_donem")
                sinif_a = c_a2.selectbox("Sınıf", ["Tümü"]+sorted(df_arsiv['Sınıf'].dropna().unique()), key="arsiv_sinif")

                df_af = df_arsiv.copy()
                if donem_a != "Tümü" and 'Donem' in df_af.columns:
                    df_af = df_af[df_af['Donem']==donem_a]
                if sinif_a != "Tümü":
                    df_af = df_af[df_af['Sınıf']==sinif_a]

                st.markdown(f"**{len(df_af)} kayıt bulundu**")

                # Tablo görünümü
                tablo_data = []
                for _, row in df_af.iterrows():
                    yorum = row.get('Genel Değerlendirme Yorumu','')
                    onayli = row.get('Onaylandi', False)
                    tablo_data.append({
                        'Okul No': row.get('Okul No',''),
                        'Öğrenci': row.get('Öğrenci Adı Soyadı',''),
                        'Sınıf': row.get('Sınıf',''),
                        'Dönem': row.get('Donem',''),
                        'Durum': '✅ Onaylı' if onayli else ('📝 Yazıldı' if yorum else '⏳ Bekliyor'),
                        'Görüş (Özet)': (yorum[:80]+'...' if len(yorum or '')>80 else yorum) if yorum else '—'
                    })
                st.dataframe(pd.DataFrame(tablo_data), use_container_width=True, hide_index=True)

                # Toplu Excel İndir
                st.markdown("---")
                c_exp1, c_exp2 = st.columns(2)
                out_arsiv = io.BytesIO()
                with pd.ExcelWriter(out_arsiv, engine='xlsxwriter') as w:
                    df_af[['Okul No','Öğrenci Adı Soyadı','Sınıf','Donem','Genel Değerlendirme Yorumu','Onaylandi']].to_excel(w, index=False, sheet_name='Arsiv')
                c_exp1.download_button(
                    "📥 Arşivi Excel Olarak İndir",
                    data=out_arsiv.getvalue(),
                    file_name=f"Karne_Arsiv_{donem_a}.xlsx",
                    use_container_width=True
                )

                # Toplu HTML Karne
                df_onayli = df_af[df_af['Onaylandi']==True] if 'Onaylandi' in df_af.columns else df_af
                if not df_onayli.empty and c_exp2.button("🖨️ Onaylı Karneleri HTML Yazdır", use_container_width=True):
                    # Karne görüş HTML (özel format)
                    html_k = """<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8">
<title>Karne Görüşleri</title>
<style>
  body{font-family:'Segoe UI',Arial,sans-serif;background:#f8fafc;padding:20px;}
  .page{background:white;max-width:680px;margin:0 auto 24px;border-radius:14px;overflow:hidden;
        box-shadow:0 4px 20px rgba(0,0,0,0.1);page-break-after:always;}
  .hdr{background:linear-gradient(135deg,#0c1e4a,#2563eb);color:white;padding:20px 24px;}
  .body{padding:22px 24px;}
  .info-row{display:flex;flex-wrap:wrap;gap:14px;background:#eff6ff;padding:14px;border-radius:10px;margin-bottom:18px;}
  .info-i{display:flex;flex-direction:column;}
  .info-l{font-size:0.7rem;color:#64748b;font-weight:700;text-transform:uppercase;}
  .info-v{font-size:0.95rem;font-weight:800;color:#0f172a;}
  .yorum{background:#fffbeb;border-left:4px solid #f59e0b;padding:16px;border-radius:8px;color:#78350f;line-height:1.7;}
  .imza{text-align:right;margin-top:18px;color:#64748b;font-size:0.82rem;}
  @media print{.page{box-shadow:none;}}
</style></head><body>"""
                    for _, row_k in df_onayli.iterrows():
                        notlar_k, davranis_k = {}, 75
                        try:
                            dj = json.loads(str(row_k.get('Dinamik_JSON','{}')))
                            notlar_k  = dj.get('notlar',{})
                            davranis_k = int(float(str(notlar_k.get('Davranış',75) or 75)))
                        except: pass
                        html_k += f"""<div class="page">
  <div class="hdr"><h2 style="margin:0">{row_k.get('Gorev_Adi','Karne Görüşü')}</h2>
    <p style="margin:4px 0 0;opacity:0.8">{row_k.get('Okul','')}</p></div>
  <div class="body">
    <div class="info-row">
      <div class="info-i"><span class="info-l">Öğrenci</span><span class="info-v">{row_k.get('Öğrenci Adı Soyadı','')}</span></div>
      <div class="info-i"><span class="info-l">Sınıf</span><span class="info-v">{row_k.get('Sınıf','')}</span></div>
      <div class="info-i"><span class="info-l">No</span><span class="info-v">{row_k.get('Okul No','')}</span></div>
      <div class="info-i"><span class="info-l">Davranış</span><span class="info-v" style="color:{'#10b981' if davranis_k>=85 else ('#f59e0b' if davranis_k>=65 else '#ef4444')}">{davranis_k}/100</span></div>
    </div>
    <div class="yorum"><strong>💬 Karne Görüşü:</strong><br><br>{row_k.get('Genel Değerlendirme Yorumu','')}</div>
    <div class="imza">Sınıf Öğretmeni: <strong>{kb.get('ad','')}</strong></div>
  </div>
</div>"""
                    html_k += "</body></html>"
                    st.download_button("📥 HTML İndir", data=html_k,
                                       file_name=f"Karne_Gorusleri_{donem_a}.html", mime="text/html")
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: YÖNETİM (Admin)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "yonetim" and rol=="admin" and not admin_bakis:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='card-baslik'>👨‍🏫 Öğretmen Yönetimi</div>", unsafe_allow_html=True)

        YON_ALT = [("ogretmenler","👨‍🏫 Öğretmenler"),("okullar","🏢 Okullar"),("ekle_ogrt","➕ Yeni Öğretmen")]
        render_sub_nav(YON_ALT, "nav_yon_alt")
        y_alt = st.session_state.get("nav_yon_alt","ogretmenler")

        if y_alt == "ogretmenler":
            if bildirim > 0:
                st.markdown(f'<div class="banner warn">⏳ {bildirim} öğretmen onay bekliyor.</div>', unsafe_allow_html=True)

            # Okul filtresi
            tum_okullar_y = sorted(set(v.get("okul","") for v in ayarlar["kullanicilar"].values()
                                       if v.get("rol")=="ogretmen" and v.get("okul")))
            sec_okul_y = st.selectbox("Okula Göre Filtrele", ["Tümü"]+tum_okullar_y)

            ogrt_filtrelendi = {k:v for k,v in ayarlar["kullanicilar"].items()
                                if v.get("rol")=="ogretmen" and
                                (sec_okul_y=="Tümü" or v.get("okul")==sec_okul_y)}

            for kadi, user in ogrt_filtrelendi.items():
                onayli   = user.get("onayli",True)
                g_sayisi = len(df[df['Atanan_Ogretmen']==kadi]) if not df.empty else 0
                avatar_r = user['ad'][0].upper() if user['ad'] else "?"

                with st.expander(f"{'✅' if onayli else '⏳'} {user['ad']} — {user.get('okul','')} ({g_sayisi} görev)", expanded=not onayli):
                    c_u1, c_u2 = st.columns([3,2])
                    with c_u1:
                        st.markdown(f"""
                        <div class="ogrt-satir {'bekliyor' if not onayli else ''}">
                            <div class="ogrt-avatar">{avatar_r}</div>
                            <div>
                                <div style="font-weight:800">{user['ad']}</div>
                                <div style="font-size:0.8rem;color:#64748b">{user.get('brans','')} · {user.get('eposta','—')}</div>
                                <div style="font-size:0.78rem;color:#94a3b8;margin-top:2px">{user.get('okul','')}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                    with c_u2:
                        if st.button("👁️ Gözat", key=f"goz_{kadi}", use_container_width=True):
                            st.session_state["admin_bakis_modu"] = True
                            st.session_state["admin_bakis_ogretmen"] = kadi
                            st.rerun()

                    # Düzenleme formu
                    with st.form(f"ogrt_form_{kadi}"):
                        fc1, fc2 = st.columns(2)
                        y_ad     = fc1.text_input("Ad Soyad", value=user['ad'], key=f"yad_{kadi}")
                        y_brans  = fc2.text_input("Branş", value=user.get('brans',''), key=f"ybr_{kadi}")
                        y_okul_i = sorted(ayarlar["okullar"]).index(user['okul']) if user['okul'] in ayarlar["okullar"] else 0
                        y_okul   = st.selectbox("Okul", sorted(ayarlar["okullar"]), index=y_okul_i, key=f"yok_{kadi}")
                        fc3, fc4 = st.columns(2)
                        y_ep     = fc3.text_input("E-posta", value=user.get('eposta',''), key=f"yep_{kadi}")
                        y_sifre  = fc4.text_input("Şifre", value=user['sifre'], type="password", key=f"ysi_{kadi}")
                        y_onay   = st.checkbox("Onaylı Hesap", value=onayli, key=f"yon_{kadi}")
                        col_fg1, col_fg2 = st.columns(2)
                        if col_fg1.form_submit_button("💾 Güncelle"):
                            ayarlar["kullanicilar"][kadi].update({
                                "ad":y_ad,"okul":y_okul,"brans":y_brans,
                                "eposta":y_ep,"sifre":y_sifre,"onayli":y_onay
                            })
                            ayar_kaydet(ayarlar)
                            st.success("✅ Güncellendi!")
                            time.sleep(1); st.rerun()
                        if col_fg2.form_submit_button("🗑️ Hesabı Sil", type="primary"):
                            del ayarlar["kullanicilar"][kadi]
                            ayar_kaydet(ayarlar)
                            st.rerun()

        elif y_alt == "okullar":
            t_ek, t_bir = st.tabs(["➕ Okul Ekle/Sil","🔗 Okulları Birleştir"])
            with t_ek:
                c_il_y, c_ilce_y, c_ok_y = st.columns(3)
                ek_il   = c_il_y.selectbox("İl", ["— Seçiniz —"]+TUM_ILLER, key="ek_il")
                ek_ilce = c_ilce_y.text_input("İlçe", key="ek_ilce").strip().title()
                ek_okul = c_ok_y.text_input("Okul Adı", key="ek_okul").strip().title()
                if st.button("➕ Ekle", type="primary"):
                    if ek_il=="— Seçiniz —" or not ek_ilce or not ek_okul:
                        st.error("İl, ilçe ve okul adı gerekli.")
                    else:
                        tam = f"{ek_il} / {ek_ilce} / {ek_okul}"
                        if tam not in ayarlar["okullar"]:
                            ayarlar["okullar"].append(tam)
                            ayar_kaydet(ayarlar)
                            st.success(f"✅ '{tam}' eklendi!")
                            time.sleep(1); st.rerun()
                        else:
                            st.warning("Zaten mevcut.")
                st.markdown("---")
                sil_ok = st.selectbox("Silinecek Okul", ["— Seçiniz —"]+sorted(ayarlar["okullar"]))
                if st.button("🗑️ Okulу Sil") and sil_ok!="— Seçiniz —":
                    ayarlar["okullar"].remove(sil_ok)
                    ayar_kaydet(ayarlar)
                    st.success("Silindi.")
                    time.sleep(1); st.rerun()

            with t_bir:
                st.markdown('<div class="banner info">Hatalı isimli okulu doğru isimli okulla birleştir. Tüm veriler aktarılır.</div>', unsafe_allow_html=True)
                c_b1, c_b2 = st.columns(2)
                hatali = c_b1.selectbox("Silinecek (Hatalı) Okul", ["— Seçiniz —"]+sorted(ayarlar["okullar"]))
                hedef  = c_b2.selectbox("Aktarılacak (Doğru) Okul", ["— Seçiniz —"]+sorted(ayarlar["okullar"]))
                if st.button("🔗 Birleştir", type="primary"):
                    if hatali=="— Seçiniz —" or hedef=="— Seçiniz —" or hatali==hedef:
                        st.error("İki farklı okul seçin.")
                    else:
                        supabase.table('gorevler').update({'okul':hedef}).eq('okul',hatali).execute()
                        for k,u in ayarlar["kullanicilar"].items():
                            if u.get("okul")==hatali:
                                ayarlar["kullanicilar"][k]["okul"] = hedef
                        if hatali in ayarlar["okullar"]:
                            ayarlar["okullar"].remove(hatali)
                        ayar_kaydet(ayarlar)
                        st.success(f"✅ Birleştirildi!")
                        time.sleep(2); st.rerun()

        elif y_alt == "ekle_ogrt":
            c_oto = st.columns(2)
            oto_onay = c_oto[0].checkbox("Otomatik Onay Aktif", value=ayarlar.get("otomatik_onay",True))
            if oto_onay != ayarlar.get("otomatik_onay",True):
                ayarlar["otomatik_onay"] = oto_onay
                ayar_kaydet(ayarlar)
                st.rerun()
            with st.form("ekle_ogrt_form"):
                e_kadi   = st.text_input("Kullanıcı Adı")
                e_ad     = st.text_input("Ad Soyad")
                ec1,ec2  = st.columns(2)
                e_okul   = ec1.selectbox("Okul", sorted(ayarlar["okullar"]))
                e_brans  = ec2.text_input("Branş")
                ec3,ec4  = st.columns(2)
                e_ep     = ec3.text_input("E-posta")
                e_si     = ec4.text_input("Şifre")
                if st.form_submit_button("➕ Ekle ve Onayla", type="primary"):
                    if e_kadi in ayarlar["kullanicilar"]:
                        st.error("Kullanıcı adı alınmış!")
                    elif e_kadi and e_si and e_ad:
                        ayarlar["kullanicilar"][e_kadi] = {
                            "sifre":e_si,"rol":"ogretmen","ad":e_ad,"okul":e_okul,
                            "brans":e_brans,"eposta":e_ep,"onayli":True
                        }
                        ayar_kaydet(ayarlar)
                        st.success("✅ Eklendi!")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: AYARLAR & PROFİL
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ayarlar":
        AYAR_ALT = ([("sistem","🔒 Sistem"),("sablonlar","📐 Şablonlar"),("profil","👤 Profil")]
                    if rol=="admin" and not admin_bakis else
                    [("profil","👤 Profil"),("sablonlar","📐 Şablonlar")])
        render_sub_nav(AYAR_ALT, "nav_ayar_alt")
        a_alt = st.session_state.get("nav_ayar_alt","profil")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        if a_alt == "sistem" and rol=="admin":
            st.markdown("<div class='card-baslik'>🔒 Sistem Kontrolü</div>", unsafe_allow_html=True)
            kilitli = st.checkbox("Sistemi Öğretmen Girişine Kapat", value=ayarlar.get("sistem_kilitli",False))
            if kilitli != ayarlar.get("sistem_kilitli",False):
                ayarlar["sistem_kilitli"] = kilitli
                ayar_kaydet(ayarlar)
                st.rerun()
            if kilitli:
                st.markdown('<div class="banner err">🔒 Sistem şu anda KAPALI.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="banner ok">✅ Sistem AÇIK — öğretmenler giriş yapabilir.</div>', unsafe_allow_html=True)

        elif a_alt == "sablonlar":
            sablon_yonetimi_ui(ayarlar, kb, rol)

        elif a_alt == "profil":
            st.markdown("<div class='card-baslik'>👤 Profilim</div>", unsafe_allow_html=True)
            with st.form("profil_form"):
                cp1, cp2 = st.columns(2)
                p_ad    = cp1.text_input("Ad Soyad", value=kb["ad"])
                p_brans = cp2.text_input("Branş", value=kb.get("brans",""))
                p_ep    = st.text_input("E-posta", value=kb.get("eposta",""))
                p_si    = st.text_input("Yeni Şifre (boş = değişmez)", type="password")
                if st.form_submit_button("💾 Güncelle"):
                    upd = {"ad":p_ad,"brans":p_brans,"eposta":p_ep}
                    if p_si.strip():
                        upd["sifre"] = p_si
                    ayarlar["kullanicilar"][aktif_id].update(upd)
                    ayar_kaydet(ayarlar)
                    st.session_state["kullanici_bilgi"] = ayarlar["kullanicilar"][aktif_id]
                    st.success("✅ Güncellendi!")

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 15. FOOTER
# ==========================================
def footer_goster():
    st.markdown("""
    <div class="app-footer">
        <strong style="color:white;font-size:1rem;">🧭 PUSULA 360</strong><br>
        Bütüncül Proje, Performans ve Karne Değerlendirme Platformu<br>
        Dargeçit İlçe Milli Eğitim Müdürlüğü<br><br>
        Tasarım: <strong style="color:white;">Sıraç AKSAN</strong> &nbsp;·&nbsp;
        <a href="mailto:saracaksan@gmail.com">saracaksan@gmail.com</a> &nbsp;·&nbsp;
        0506 928 22 10<br>
        <small style="color:#475569;">© 2025 PUSULA 360. Tüm hakları saklıdır.</small>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 16. ANA ÇALIŞTIRMA
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df      = veri_yukle()

    st.markdown("""
    <div class="p360-hero">
        <div class="p360-hero-title">🧭 PUSULA 360</div>
        <div class="p360-hero-sub">Bütüncül Proje, Performans ve Karne Değerlendirme Platformu</div>
        <span class="p360-hero-badge">Dargeçit İlçe Milli Eğitim Müdürlüğü</span>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("giris_yapti", False):
        giris_ekrani(df, ayarlar)
    else:
        yonetim_paneli(df, ayarlar)

    footer_goster()

if __name__ == "__main__":
    main()
