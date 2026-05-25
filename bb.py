import streamlit as st
import pandas as pd
import io
import os
import json
import requests
import time

# ==========================================
# SAYFA YAPILANDIRMASI VE TEMA
# ==========================================
st.set_page_config(
    page_title="Gazi Ortaokulu | Proje Değerlendirme Sistemi",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Varsayılan Öğretmen Bilgileri (Session State Başlatma)
if "ogretmen_adi" not in st.session_state:
    st.session_state["ogretmen_adi"] = "Sıraç AKSAN"
if "ogretmen_bransi" not in st.session_state:
    st.session_state["ogretmen_bransi"] = "Matematik"

# ─── ÖZEL CSS TASARIM ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Inter:wght@400;500;600&display=swap');

/* GENEL ARKAPLAN */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2044 100%);
    min-height: 100vh;
}

/* BAŞLIK ALANI */
.hero-header {
    background: linear-gradient(135deg, #1e40af, #3b82f6, #60a5fa);
    border-radius: 20px;
    padding: 32px 40px;
    margin-bottom: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4);
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
    animation: shimmer 4s infinite;
}
@keyframes shimmer {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.hero-title {
    font-family: 'Nunito', sans-serif;
    font-size: 2.4rem;
    font-weight: 900;
    color: white;
    margin: 0 0 6px 0;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.85);
    margin: 0;
    font-weight: 500;
}

/* TAB STILI */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 6px;
    border: 1px solid rgba(255,255,255,0.1);
    gap: 4px;
    margin-bottom: 20px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent;
    border-radius: 12px;
    color: rgba(255,255,255,0.6);
    font-weight: 600;
    font-size: 0.95rem;
    padding: 10px 24px;
    border: none;
    transition: all 0.25s ease;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.08);
    color: white;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    color: white !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.5);
}

/* KART BİLEŞENLERİ */
.glass-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 18px;
    backdrop-filter: blur(12px);
}
.metric-card {
    background: linear-gradient(135deg, rgba(37,99,235,0.3), rgba(59,130,246,0.15));
    border: 1px solid rgba(96,165,250,0.3);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(8px);
}
.metric-card .metric-value {
    font-family: 'Nunito', sans-serif;
    font-size: 2.4rem;
    font-weight: 900;
    color: #60a5fa;
    line-height: 1;
}
.metric-card .metric-label {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.55);
    margin-top: 6px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* INPUT ALANLARI (Görünmez Metin Sorunu Çözüldü) */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background-color: #1e293b !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    background-color: #0f172a !important;
    border-color: #60a5fa !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
    color: rgba(255,255,255,0.75) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* BUTONLAR */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 700 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.95rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4) !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.6) !important;
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* İNDİRME BUTONU */
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 16px rgba(5, 150, 105, 0.4) !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(5, 150, 105, 0.6) !important;
}

/* UYARI VE BİLGİ MESAJLARI */
.stSuccess { background: rgba(16, 185, 129, 0.15) !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; border-radius: 12px !important; }
.stError { background: rgba(239, 68, 68, 0.15) !important; border: 1px solid rgba(239, 68, 68, 0.3) !important; border-radius: 12px !important; }
.stWarning { background: rgba(245, 158, 11, 0.15) !important; border: 1px solid rgba(245, 158, 11, 0.3) !important; border-radius: 12px !important; }
.stInfo { background: rgba(59, 130, 246, 0.15) !important; border: 1px solid rgba(59, 130, 246, 0.3) !important; border-radius: 12px !important; }

/* TABLO */
.stDataFrame { background: rgba(255,255,255,0.04) !important; border-radius: 14px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }

/* PROGRESS BAR */
.puan-bar-wrapper {
    width: 100%;
    height: 8px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    overflow: hidden;
    margin-top: 4px;
}
.puan-bar-fill {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    transition: width 0.6s ease;
}

/* KRITER KUTUSU */
.kriter-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 14px;
    transition: border-color 0.2s;
}
.kriter-box:hover {
    border-color: rgba(59, 130, 246, 0.4);
}
.kriter-baslik {
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    color: #93c5fd;
    font-size: 0.95rem;
    margin-bottom: 4px;
}
.kriter-aciklama {
    color: rgba(255,255,255,0.45);
    font-size: 0.78rem;
    margin-bottom: 12px;
    font-style: italic;
}

/* AI BUTONU ÖZEL */
.ai-btn > button {
    background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.5) !important;
}
.ai-btn > button:hover {
    background: linear-gradient(135deg, #6d28d9, #7c3aed) !important;
    box-shadow: 0 8px 28px rgba(124, 58, 237, 0.7) !important;
}

/* KAYDET BUTONU ÖZEL */
.kaydet-btn > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    box-shadow: 0 4px 20px rgba(5, 150, 105, 0.5) !important;
}

/* EXPANDER */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
}

/* RADİO BUTON */
.stRadio > div { flex-direction: row; gap: 16px; flex-wrap: wrap; }
.stRadio label {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    color: white !important;
    cursor: pointer !important;
}

/* FORM */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 20px;
}

/* TOPLAM PUAN BADGE */
.toplam-badge {
    background: linear-gradient(135deg, #dc2626, #ef4444);
    color: white;
    font-family: 'Nunito', sans-serif;
    font-size: 2rem;
    font-weight: 900;
    border-radius: 16px;
    padding: 16px 32px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(220, 38, 38, 0.4);
    display: inline-block;
    min-width: 120px;
}

/* SCROLLBAR */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.35); }

/* DIVIDER */
.custom-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    margin: 20px 0;
}

/* SELECTBOX / MULTISELECT GÖRÜNÜM DÜZELTMELERİ */
div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 10px !important;
    color: white !important;
}
div[data-baseweb="popover"] {
    background-color: #1e293b !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 10px !important;
}
ul[data-baseweb="menu"] {
    background-color: #1e293b !important;
}
ul[data-baseweb="menu"] li {
    color: white !important;
    background-color: transparent !important;
}
ul[data-baseweb="menu"] li:hover {
    background-color: rgba(59,130,246,0.3) !important;
    color: white !important;
}
span[data-baseweb="tag"] {
    background-color: rgba(59,130,246,0.2) !important;
    border: 1px solid rgba(59,130,246,0.5) !important;
    color: white !important;
}
.stNumberInput button { background: rgba(255,255,255,0.1) !important; border: none !important; color: white !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# VERİTABANI VE SABİTLER
# ==========================================

DATA_FILE = "veritabani.csv"

# ==========================================
# GÜVENLİ API VE BAĞLANTI AYARLARI
# ==========================================

# 1. Eğer yerel bilgisayarında çalışıyorsan, streamlit secrets.toml dosyası yoksa diye
# aşağıdaki satır hata vermemesi için "try-except" yapısına alındı.
try:
    API_KEY = st.secrets["API_KEY"]
except:
    # Yerel geliştirmede anahtarı doğrudan buraya yazabilirsin, 
    # ama GitHub'a yüklerken mutlaka anahtarı silip secrets'a ekle!
    API_KEY = "AIzaSyDR59-y8bOekDJBHjSN9vvFfjhWXQfPRUM" 

# Google Generative AI kütüphanesini en yeni beta URL ile kullanmak için yapılandırma
genai.configure(api_key=API_KEY)

# Yapay Zeka Modeli (En güncel model)
model = genai.GenerativeModel('gemini-1.5-flash')

# Eğer manuel API çağrısı yapacaksan (url üzerinden) kullanacağın yapı:
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

KRITERLER = [
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu",  "max": 40, "icon": "📚",
     "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi ve konu hakimiyeti."},
    {"id": "k2", "baslik": "Düzen ve Tertip",              "max": 15, "icon": "📐",
     "aciklama": "Ödevin temiz, okunaklı ve düzenli hazırlanmış olması. Kağıt kullanımının özeni."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍",
     "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler veya açıklamalar eklenmesi."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum",        "max": 15, "icon": "🎨",
     "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi."},
    {"id": "k5", "baslik": "Zamanında Teslim",            "max": 15, "icon": "⏰",
     "aciklama": "Projenin belirtilen tarihte (26 Nisan 2026) teslim edilmesi."},
]

GEREKLI_SUTUNLAR = ['S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', '1. Dönem Puanı', 'Proje', 'Durum']
for _k in KRITERLER:
    GEREKLI_SUTUNLAR.append(f"{_k['baslik']} Puanı")
    GEREKLI_SUTUNLAR.append(f"{_k['baslik']} Açıklaması")
GEREKLI_SUTUNLAR.extend(['Genel Değerlendirme Yorumu', 'Toplam Puan'])


# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================

@st.cache_data(ttl=0)
def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype={"Okul No": str})
            df.dropna(subset=['Okul No'], inplace=True)
            df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
            for s in GEREKLI_SUTUNLAR:
                if s not in df.columns:
                    df[s] = None
            return df
        except Exception:
            return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
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
        ws = writer.sheets['Ogrenci_Sablonu']
        for col_num, val in enumerate(sablon_df.columns.values):
            ws.set_column(col_num, col_num, 22)
    return output.getvalue()


def puan_renk(puan, max_puan):
    oran = puan / max_puan if max_puan > 0 else 0
    if oran >= 0.85:
        return "#10b981"
    elif oran >= 0.60:
        return "#f59e0b"
    else:
        return "#ef4444"


def karne_html_olustur(bilgi, ogrt_ad, ogrt_brans):
    toplam_puan = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
    toplam_puan = 0 if pd.isna(toplam_puan) else int(toplam_puan)
    renk = puan_renk(toplam_puan, 100)

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif; background:white; border-radius:16px; overflow:hidden; box-shadow:0 8px 40px rgba(0,0,0,0.15);">
      <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb); padding:24px 32px; color:white;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="font-size:11px; opacity:0.7; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px;">Gazi Ortaokulu · {ogrt_brans} Birimi</div>
            <div style="font-size:1.4rem; font-weight:800; letter-spacing:-0.3px;">Proje Değerlendirme Karnesi</div>
          </div>
          <div style="background:rgba(255,255,255,0.15); border-radius:12px; padding:12px 20px; text-align:center; backdrop-filter:blur(4px);">
            <div style="font-size:2.2rem; font-weight:900; color:{renk}; background:white; border-radius:8px; padding:6px 16px; display:inline-block;">{toplam_puan}</div>
            <div style="font-size:0.7rem; opacity:0.7; margin-top:4px;">TOPLAM / 100</div>
          </div>
        </div>
      </div>

      <div style="background:#f8fafc; padding:16px 32px; border-bottom:2px solid #e2e8f0; display:flex; gap:32px; flex-wrap:wrap;">
        <div><span style="color:#64748b; font-size:0.75rem; font-weight:600; text-transform:uppercase;">👤 Öğrenci</span><br><span style="color:#1e293b; font-weight:700; font-size:1rem;">{bilgi.get('Öğrenci Adı Soyadı','')}</span></div>
        <div><span style="color:#64748b; font-size:0.75rem; font-weight:600; text-transform:uppercase;">🏫 Sınıf</span><br><span style="color:#1e293b; font-weight:700; font-size:1rem;">{bilgi.get('Sınıf','')}</span></div>
        <div><span style="color:#64748b; font-size:0.75rem; font-weight:600; text-transform:uppercase;">🔢 Okul No</span><br><span style="color:#1e293b; font-weight:700; font-size:1rem;">{bilgi.get('Okul No','')}</span></div>
        <div><span style="color:#64748b; font-size:0.75rem; font-weight:600; text-transform:uppercase;">📖 Proje</span><br><span style="color:#1e293b; font-weight:700; font-size:1rem;">{bilgi.get('Proje','-')}</span></div>
        <div><span style="color:#64748b; font-size:0.75rem; font-weight:600; text-transform:uppercase;">📅 1. Dönem</span><br><span style="color:#1e293b; font-weight:700; font-size:1rem;">{bilgi.get('1. Dönem Puanı','-')}</span></div>
      </div>

      <div style="padding:0 16px 8px;">
        <table style="width:100%; border-collapse:collapse; margin-top:12px;">
          <tr style="background:#f1f5f9;">
            <th style="padding:10px 14px; text-align:left; font-size:0.78rem; color:#475569; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; width:28%;">Kriter</th>
            <th style="padding:10px 14px; text-align:center; font-size:0.78rem; color:#475569; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; width:9%;">Max</th>
            <th style="padding:10px 14px; text-align:center; font-size:0.78rem; color:#475569; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; width:9%;">Alınan</th>
            <th style="padding:10px 14px; text-align:left; font-size:0.78rem; color:#475569; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; width:54%;">Öğretmen / Yapay Zeka Değerlendirmesi</th>
          </tr>
    """

    for i, k in enumerate(KRITERLER):
        puan = pd.to_numeric(bilgi.get(f"{k['baslik']} Puanı", 0), errors='coerce')
        puan = 0 if pd.isna(puan) else int(puan)
        aciklama = bilgi.get(f"{k['baslik']} Açıklaması", "")
        aciklama = "Değerlendirme henüz girilmedi." if pd.isna(aciklama) or str(aciklama).strip() == "" else str(aciklama)
        r = puan_renk(puan, k['max'])
        oran = int((puan / k['max']) * 100) if k['max'] > 0 else 0
        bg = "#ffffff" if i % 2 == 0 else "#f8fafc"

        html += f"""
          <tr style="background:{bg}; border-bottom:1px solid #e2e8f0;">
            <td style="padding:12px 14px;">
              <div style="font-weight:700; color:#1e293b; font-size:0.88rem;">{k['icon']} {k['baslik']}</div>
              <div style="font-size:0.72rem; color:#94a3b8; margin-top:2px;">{k['aciklama']}</div>
            </td>
            <td style="padding:12px 14px; text-align:center; color:#475569; font-weight:600;">{k['max']}</td>
            <td style="padding:12px 14px; text-align:center;">
              <span style="color:{r}; font-size:1.3rem; font-weight:900;">{puan}</span>
              <div style="width:100%; height:4px; background:#e2e8f0; border-radius:4px; margin-top:4px; overflow:hidden;">
                <div style="width:{oran}%; height:100%; background:{r}; border-radius:4px;"></div>
              </div>
            </td>
            <td style="padding:12px 14px; color:#2d6a4f; font-size:0.85rem; font-style:italic; line-height:1.5;">{aciklama}</td>
          </tr>
        """

    genel_yorum = bilgi.get('Genel Değerlendirme Yorumu', '')
    genel_yorum = "Henüz genel değerlendirme yapılmadı." if pd.isna(genel_yorum) or str(genel_yorum).strip() == "" else str(genel_yorum)

    html += f"""
        </table>
      </div>

      <div style="margin:12px 16px 16px; background:#eff6ff; border-left:4px solid #3b82f6; border-radius:0 12px 12px 0; padding:14px 18px;">
        <div style="font-size:0.75rem; font-weight:700; color:#1d4ed8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">💬 Genel Değerlendirme</div>
        <div style="color:#1e40af; font-size:0.9rem; line-height:1.6;">{genel_yorum}</div>
      </div>

      <div style="background:#f8fafc; border-top:1px solid #e2e8f0; padding:14px 32px; display:flex; justify-content:space-between; align-items:center;">
        <div style="font-size:0.78rem; color:#94a3b8;">Gazi Ortaokulu · {ogrt_brans} Dersi · 2025-2026</div>
        <div style="text-align:right; font-size:0.82rem; color:#475569;">
          <div style="font-weight:700; color:#1e293b;">{ogrt_ad}</div>
          <div style="font-size:0.72rem; color:#94a3b8;">{ogrt_brans} Öğretmeni</div>
        </div>
      </div>
    </div>
    """
    return html


def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans):
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Proje Karneleri – Gazi Ortaokulu</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Nunito:wght@700;900&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; background: #f1f5f9; }}
  .page {{ background: white; width: 210mm; margin: 12mm auto; padding: 14mm 16mm; border-radius: 4px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); page-break-after: always; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #1e3a8a; color: white; padding: 9px 12px; font-size: 0.72rem; text-align: left; }}
  td {{ padding: 9px 12px; font-size: 0.82rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  .header {{ background: linear-gradient(135deg,#1e3a8a,#2563eb); color:white; padding:16px 20px; border-radius:8px; margin-bottom:14px; }}
  .bilgi-row {{ display:flex; gap:24px; margin-bottom:12px; font-size:0.85rem; flex-wrap:wrap; }}
  .bilgi-row span {{ color:#475569; }}
  .bilgi-row strong {{ color:#1e293b; }}
  .yorum {{ background:#eff6ff; border-left:3px solid #3b82f6; padding:10px 14px; margin-top:10px; font-size:0.82rem; color:#1e40af; border-radius:0 8px 8px 0; }}
  .imza {{ margin-top:20px; text-align:right; font-size:0.8rem; color:#475569; border-top:1px solid #e2e8f0; padding-top:10px; }}
  @media print {{ body{{background:white;}} .page{{box-shadow:none; margin:0; border-radius:0; width:100%;}} }}
</style>
</head>
<body>
"""
    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam = pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce')
        toplam = 0 if pd.isna(toplam) else int(toplam)
        renk = "#10b981" if toplam >= 85 else ("#f59e0b" if toplam >= 60 else "#ef4444")

        html += f"""
<div class="page">
  <div class="header">
    <div style="font-size:0.7rem;opacity:0.7;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Gazi Ortaokulu · {ogrt_brans} Birimi · 2025-2026</div>
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div style="font-size:1.2rem;font-weight:800;">Proje Değerlendirme Karnesi</div>
      <div style="background:white;color:{renk};font-size:1.8rem;font-weight:900;padding:6px 16px;border-radius:8px;">{toplam}<span style="font-size:0.8rem;color:#64748b;">/100</span></div>
    </div>
  </div>
  <div class="bilgi-row">
    <div><span>👤 Öğrenci: </span><strong>{b.get('Öğrenci Adı Soyadı','')}</strong></div>
    <div><span>🏫 Sınıf: </span><strong>{b.get('Sınıf','')}</strong></div>
    <div><span>🔢 No: </span><strong>{b.get('Okul No','')}</strong></div>
    <div><span>📖 Proje: </span><strong>{b.get('Proje','-')}</strong></div>
    <div><span>1. Dönem: </span><strong>{b.get('1. Dönem Puanı','-')}</strong></div>
  </div>
  <table>
    <tr><th>Kriter</th><th style="width:60px;text-align:center;">Max</th><th style="width:70px;text-align:center;">Alınan</th><th>Değerlendirme</th></tr>
"""
        for k in KRITERLER:
            p = pd.to_numeric(b.get(f"{k['baslik']} Puanı", 0), errors='coerce')
            p = 0 if pd.isna(p) else int(p)
            a = b.get(f"{k['baslik']} Açıklaması", "")
            a = "-" if pd.isna(a) or str(a).strip() == "" else str(a)
            r2 = puan_renk(p, k['max'])
            html += f"<tr><td><strong>{k['icon']} {k['baslik']}</strong><br><span style='font-size:0.7rem;color:#94a3b8;'>{k['aciklama']}</span></td><td style='text-align:center;color:#475569;font-weight:600;'>{k['max']}</td><td style='text-align:center;color:{r2};font-size:1.1rem;font-weight:900;'>{p}</td><td style='color:#2d6a4f;font-style:italic;'>{a}</td></tr>"

        genel = b.get('Genel Değerlendirme Yorumu', '')
        genel = "Değerlendirme girilmedi." if pd.isna(genel) or str(genel).strip() == "" else str(genel)
        html += f"""
  </table>
  <div class="yorum"><strong>💬 Genel Değerlendirme:</strong> {genel}</div>
  <div class="imza"><strong>{ogrt_ad}</strong> · {ogrt_brans} Öğretmeni</div>
</div>
"""
    html += "</body></html>"
    return html


# ==========================================
# AI FONKSİYONU — GEMINI API ENTEGRASYONU
# ==========================================

def ai_degerlendirme_yap(bilgi_dict: dict, ham_metin: str, puanlar: dict, ogrt_ad: str, ogrt_brans: str) -> dict:
    """Gemini API'yi çağırarak değerlendirme metinleri üretir."""
    puan_ozeti = "\n".join([
        f"  - {k['baslik']}: {puanlar.get(k['id'], 0)}/{k['max']}"
        for k in KRITERLER
    ])

    prompt = f"""Sen Gazi Ortaokulu'nda görev yapan deneyimli, anlayışlı ve motive edici bir ortaokul {ogrt_brans.lower()} öğretmenisin. Adın {ogrt_ad}.

Öğrencinin proje puanları:
{puan_ozeti}

{ogrt_ad} Öğretmenin Özel Talimatı / Ek Notu:
"{ham_metin if ham_metin.strip() else 'Özel bir not girilmedi. Standart değerlendirme yap.'}"

GÖREVLER:
1) Yukarıdaki "{ogrt_ad} Öğretmenin Özel Talimatı" kısmında öğretmenin belirttiği özel durumlar, yönlendirmeler, eleştiriler veya övgüler varsa, bunları MUTLAKA ilgili kriter açıklamalarına ve genel yoruma harmanlayarak yedir.
2) Her kriter (k1, k2, k3, k4, k5) için öğrenciye doğrudan "Sen" diliyle hitap eden, öğretmen notunu da dikkate alan 1-2 cümlelik yapıcı ve motive edici açıklama yaz.
   - Puan yüksekse (≥%85): Samimi ve sıcak bir şekilde tebrik et.
   - Puan orta ise (%60-84): Olumlu yönü öne çıkar, gelişim önerisi sun.
   - Puan düşükse (<%60): Asla cesaretini kırma; eksikliği şefkatle belirt ve nasıl düzelteceğini söyle.
3) "genel" isimli ana yorum kısmını şu üç sıraya göre oluştur:
   a) Önce {ogrt_brans.lower()} dersinin günlük hayattaki öneminden kısaca bahset.
   b) Ardından öğrencinin aldığı puanlara ve özellikle ÖĞRETMENİN ÖZEL TALİMATINA göre genel durumunu şefkatle izah et.
   c) Son olarak {ogrt_brans.lower()} dersine nasıl çalışması gerektiğiyle ilgili somut, motive edici bir tavsiye vererek bitir.

KURALLLAR:
- Sadece ve sadece aşağıdaki JSON formatını döndür. Asla markdown tagleri kullanma.

{{
  "k1": "İçerik açıklaması",
  "k2": "Düzen açıklaması",
  "k3": "Araştırma açıklaması",
  "k4": "Sunum açıklaması",
  "k5": "Zamanında teslim açıklaması",
  "genel": "{ogrt_brans} dersinin önemi -> Öğretmen notuna dayalı genel durum izahı -> Nasıl çalışması gerektiği tavsiyesi"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    response.raise_for_status()
    data = response.json()
    
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw)


# ==========================================
# ÖĞRENCİ PANELİ (GÜNCELLENDİ - İndirme Butonu Eklendi)
# ==========================================

def ogrenci_paneli(df):
    st.markdown("""
    <div style="text-align:center; margin-bottom:28px;">
      <div style="font-size:3.5rem; margin-bottom:8px;">🎓</div>
      <div style="font-size:1.5rem; font-weight:800; color:white; font-family:'Nunito',sans-serif;">Proje Sonuç Sorgulama</div>
      <div style="color:rgba(255,255,255,0.55); font-size:0.9rem; margin-top:4px;">Sınıfınızı seçin ve okul numaranızı girerek proje karnenize ulaşın</div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty or len(df.columns) < 10:
        st.warning("⚠️ Sisteme henüz veri yüklenmemiştir. Lütfen öğretmeninizle iletişime geçin.")
        return

    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        siniflar = ["— Sınıf Seçiniz —"] + sorted(df['Sınıf'].dropna().unique().tolist())
        sinif = st.selectbox("🏫 Sınıfınız", siniflar, key="ogr_sinif")
        okul_no = st.text_input("🔢 Okul Numaranız", placeholder="Örnek: 1234", key="ogr_no")

        aralik = st.columns([1, 2, 1])
        with aralik[1]:
            sorgula = st.button("🔍  Sonucumu Göster", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    if sorgula:
        if sinif == "— Sınıf Seçiniz —" or not okul_no.strip():
            st.error("❌ Lütfen sınıfınızı seçin ve okul numaranızı girin.")
        else:
            ogrenci = df[(df['Sınıf'] == sinif) & (df['Okul No'] == okul_no.strip())]
            if ogrenci.empty:
                st.error("❌ Bu bilgilere ait kayıt bulunamadı. Lütfen numaranızı kontrol edin.")
            else:
                bilgi = ogrenci.iloc[0]
                toplam = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
                toplam = 0 if pd.isna(toplam) else int(toplam)

                st.success(f"✅ Hoş geldiniz, {bilgi.get('Öğrenci Adı Soyadı', '')}!")
                st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{toplam}</div><div class="metric-label">Toplam Puan</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-card"><div class="metric-value" style="font-size:1.4rem;">{bilgi.get("Sınıf","")}</div><div class="metric-label">Sınıf</div></div>', unsafe_allow_html=True)
                with m3:
                    d1_puan = bilgi.get('1. Dönem Puanı', '-')
                    st.markdown(f'<div class="metric-card"><div class="metric-value" style="font-size:1.4rem;">{d1_puan}</div><div class="metric-label">1. Dönem Puanı</div></div>', unsafe_allow_html=True)
                with m4:
                    durum = bilgi.get('Durum', '-')
                    st.markdown(f'<div class="metric-card"><div class="metric-value" style="font-size:1.1rem;">{durum}</div><div class="metric-label">Proje Durumu</div></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Güncel öğretmen ayarlarını çek
                guncel_ad = st.session_state.get("ogretmen_adi", "Sıraç AKSAN")
                guncel_brans = st.session_state.get("ogretmen_bransi", "Matematik")
                
                # Ekranda karnenin görüntüsü
               # Güncel öğretmen ayarlarını çek
                guncel_ad = st.session_state.get("ogretmen_adi", "Sıraç AKSAN")
                guncel_brans = st.session_state.get("ogretmen_bransi", "Matematik")
                
                # Tablo yerine öğrenciye özel yönlendirici ve sıcak bir açıklama metni
                st.info(f"Sevgili {bilgi.get('Öğrenci Adı Soyadı', '')}, proje değerlendirmen {guncel_brans} öğretmenin {guncel_ad} tarafından tamamlandı. Tüm kriter bazlı puanlamalarını, öğretmeninin sana özel yazdığı notları ve detaylı değerlendirme karneni görmek için aşağıdaki butona tıklayarak belgeni cihazına indirebilirsin.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Öğrencinin indirmesi için tek kişilik çıktı üretimi
                tek_ogrenci_df = pd.DataFrame([bilgi])
                indirilecek_html = toplu_karne_html_dosyasi_uret(tek_ogrenci_df, guncel_ad, guncel_brans)
                
                # İndirme Butonunu tam ortaya hizalama
                c_bos1, c_indir, c_bos2 = st.columns([1, 2, 1])
                with c_indir:
                    st.download_button(
                        label="🖨️ Detaylı Karnemi İndir (PDF/HTML)",
                        data=indirilecek_html,
                        file_name=f"{bilgi.get('Okul No', 'Ogrenci')}_{bilgi.get('Öğrenci Adı Soyadı', 'Karne').replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True,
                        help="İndirdiğiniz dosyayı açıp sağ tıklayarak veya Ctrl+P tuşlarına basarak PDF olarak kaydedebilirsiniz."
                    )
                
               








# ==========================================
# ÖĞRETMEN PANELİ
# ==========================================

def ogretmen_paneli(df):
    if "ogretmen_giris" not in st.session_state:
        st.session_state["ogretmen_giris"] = False

    if not st.session_state["ogretmen_giris"]:
        col_l, col_m, col_r = st.columns([1, 1.2, 1])
        with col_m:
            st.markdown("""
            <div style="text-align:center; margin-bottom:32px;">
              <div style="font-size:3rem; margin-bottom:8px;">🔐</div>
              <div style="font-size:1.4rem; font-weight:800; color:white; font-family:'Nunito',sans-serif;">Yönetici Girişi</div>
              <div style="color:rgba(255,255,255,0.5); font-size:0.85rem; margin-top:6px;">Devam etmek için yönetici şifresini girin</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="glass-card" style="padding:32px;">', unsafe_allow_html=True)
            sifre = st.text_input("Yönetici Şifresi", type="password", placeholder="••••••••", key="admin_pass_input")
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b2:
                if st.button("🚀  Giriş Yap", use_container_width=True, key="login_btn"):
                    if sifre == "Sarac.47":
                        st.session_state["ogretmen_giris"] = True
                        st.rerun()
                    elif sifre:
                        st.error("❌ Hatalı şifre! Lütfen tekrar deneyin.")
            st.markdown('</div>', unsafe_allow_html=True)
        return

    guncel_ad = st.session_state["ogretmen_adi"]
    guncel_brans = st.session_state["ogretmen_bransi"]

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:14px; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.25); border-radius:14px; padding:14px 20px; margin-bottom:20px;">
      <span style="font-size:1.8rem;">👋</span>
      <div>
        <div style="font-weight:700; color:#6ee7b7; font-family:'Nunito',sans-serif; font-size:1.05rem;">Hoş Geldiniz, {guncel_ad}!</div>
        <div style="color:rgba(255,255,255,0.5); font-size:0.82rem;">Gazi Ortaokulu · {guncel_brans} Proje Yönetim Paneli · 2025-2026</div>
      </div>
      <div style="margin-left:auto;">
    """, unsafe_allow_html=True)

    if st.button("🚪 Çıkış", key="logout_btn"):
        st.session_state["ogretmen_giris"] = False
        st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)

    # SEKMELER (Ayarlar sekmesi eklendi)
    otab1, otab2, otab3, otab4, otab5 = st.tabs([
        "📂 Toplu Veri Yükleme",
        "👤 Öğrenci İşlemleri",
        "🤖 Puanlama & Yapay Zeka",
        "📊 Rapor & Karne Çıktısı",
        "⚙️ Ayarlar & Profil"
    ])

    with otab1:
        st.markdown("### 📥 Şablon ve Veri Yükleme")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("#### ⬇️ Boş Şablon İndir")
            st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Excel şablonunu bilgisayarınıza indirin, öğrenci bilgilerini doldurun ve geri yükleyin.</p>', unsafe_allow_html=True)
            st.download_button(
                label="📄  Excel Şablonunu İndir",
                data=bos_sablon_olustur(),
                file_name="Ogrenci_Veri_Sablonu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("#### 📤 Doldurulmuş Dosyayı Yükle")
            st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Sadece sistemde olmayan yeni öğrenciler eklenir. Mevcut kayıtlara dokunulmaz.</p>', unsafe_allow_html=True)
            yuklenen = st.file_uploader("Dosya Seçin (.xlsx / .csv)", type=['xlsx', 'csv'], label_visibility="collapsed")
            if yuklenen:
                if st.button("💾  Verileri Kaydet", use_container_width=True, key="bulk_save"):
                    try:
                        yeni_df = pd.read_csv(yuklenen, dtype={"Okul No": str}) if yuklenen.name.endswith('.csv') else pd.read_excel(yuklenen, dtype={"Okul No": str})
                        yeni_df['Okul No'] = yeni_df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
                        yeni_df.dropna(subset=['Okul No'], inplace=True)
                        eklenecek = yeni_df[~yeni_df['Okul No'].isin(df['Okul No'].tolist())]
                        if eklenecek.empty:
                            st.warning("⚠️ Tüm öğrenciler zaten kayıtlı!")
                        else:
                            for s in GEREKLI_SUTUNLAR:
                                if s not in eklenecek.columns:
                                    eklenecek = eklenecek.copy()
                                    eklenecek[s] = None
                            df = pd.concat([df, eklenecek], ignore_index=True)
                            veriyi_kaydet(df)
                            st.success(f"✅ {len(eklenecek)} yeni öğrenci başarıyla eklendi!")
                            time.sleep(0.8)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        if not df.empty:
            st.markdown("---")
            st.markdown("#### 📈 Genel İstatistikler")
            total_ogrenci = len(df)
            degerlendirilmis = df['Toplam Puan'].notna().sum()
            sinif_sayisi = df['Sınıf'].nunique()
            ort_puan = pd.to_numeric(df['Toplam Puan'], errors='coerce').mean()

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{total_ogrenci}</div><div class="metric-label">Toplam Öğrenci</div></div>', unsafe_allow_html=True)
            with s2:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{degerlendirilmis}</div><div class="metric-label">Değerlendirilen</div></div>', unsafe_allow_html=True)
            with s3:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{sinif_sayisi}</div><div class="metric-label">Sınıf Sayısı</div></div>', unsafe_allow_html=True)
            with s4:
                ort_str = f"{ort_puan:.1f}" if not pd.isna(ort_puan) else "—"
                st.markdown(f'<div class="metric-card"><div class="metric-value">{ort_str}</div><div class="metric-label">Sınıf Ortalaması</div></div>', unsafe_allow_html=True)

    with otab2:
        st.markdown("### 👤 Öğrenci İşlemleri")
        islem = st.radio("İşlem Türü:", ["➕ Yeni Öğrenci Ekle", "✏️ Mevcut Öğrenciyi Güncelle", "🗑️ Öğrenci Sil"],
                         horizontal=True, label_visibility="collapsed")

        if islem == "➕ Yeni Öğrenci Ekle":
            with st.form("yeni_ogrenci_form", clear_on_submit=True):
                st.markdown('<div class="glass-card" style="padding:20px;">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    yeni_no = st.text_input("Okul Numarası *", placeholder="Zorunlu alan")
                    yeni_ad = st.text_input("Ad Soyad *", placeholder="Zorunlu alan")
                with c2:
                    yeni_sinif = st.text_input("Sınıf *", placeholder="Örn: 6/A")
                    yeni_puan = st.text_input("1. Dönem Puanı", placeholder="Opsiyonel")
                with c3:
                    yeni_proje = st.text_input("Proje Konusu", placeholder="Opsiyonel")
                    yeni_durum = st.selectbox("Durum", ["Zorunlu", "Gönüllü", "Proje Üst"])
                st.markdown('</div>', unsafe_allow_html=True)

                col_btn = st.columns([1, 1, 1])
                with col_btn[1]:
                    kaydet = st.form_submit_button("💾  Öğrenciyi Kaydet", use_container_width=True)

                if kaydet:
                    if not yeni_no.strip() or not yeni_ad.strip() or not yeni_sinif.strip():
                        st.error("❌ Yıldızlı alanları doldurun.")
                    elif yeni_no.strip() in df['Okul No'].tolist():
                        st.error("❌ Bu okul numarası zaten kayıtlı!")
                    else:
                        yeni_veri = {col: None for col in GEREKLI_SUTUNLAR}
                        yeni_veri.update({'Okul No': yeni_no.strip(), 'Öğrenci Adı Soyadı': yeni_ad.strip(),
                                          'Sınıf': yeni_sinif.strip(), '1. Dönem Puanı': yeni_puan,
                                          'Proje': yeni_proje, 'Durum': yeni_durum})
                        df.loc[len(df)] = yeni_veri
                        veriyi_kaydet(df)
                        st.success(f"✅ {yeni_ad} sisteme eklendi!")
                        st.rerun()

        elif islem == "✏️ Mevcut Öğrenciyi Güncelle":
            if df.empty:
                st.warning("⚠️ Güncellenecek öğrenci yok.")
            else:
                ogr_liste = df.apply(lambda r: f"{r['Sınıf']} — {r['Okul No']} — {r.get('Öğrenci Adı Soyadı','')}", axis=1).tolist()
                secim = st.selectbox("Öğrenci Seçin:", ["— Seçiniz —"] + ogr_liste)
                if secim != "— Seçiniz —":
                    okul_no_sec = secim.split(" — ")[1]
                    idx = df.index[df['Okul No'] == okul_no_sec].tolist()[0]
                    with st.form("guncelle_form"):
                        st.markdown('<div class="glass-card" style="padding:20px;">', unsafe_allow_html=True)
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            gun_ad = st.text_input("Ad Soyad", value=str(df.at[idx, 'Öğrenci Adı Soyadı'] or ""))
                            gun_sinif = st.text_input("Sınıf", value=str(df.at[idx, 'Sınıf'] or ""))
                        with c2:
                            gun_puan = st.text_input("1. Dönem Puanı", value=str(df.at[idx, '1. Dönem Puanı'] or ""))
                            gun_proje = st.text_input("Proje Konusu", value=str(df.at[idx, 'Proje'] or ""))
                        with c3:
                            durum_ops = ["Zorunlu", "Gönüllü", "Proje Üst"]
                            d_idx = durum_ops.index(df.at[idx, 'Durum']) if df.at[idx, 'Durum'] in durum_ops else 0
                            gun_durum = st.selectbox("Durum", durum_ops, index=d_idx)
                        st.markdown('</div>', unsafe_allow_html=True)

                        col_btn2 = st.columns([1, 1, 1])
                        with col_btn2[1]:
                            guncelle = st.form_submit_button("✏️  Güncelle", use_container_width=True)
                        if guncelle:
                            df.at[idx, 'Öğrenci Adı Soyadı'] = gun_ad.strip()
                            df.at[idx, 'Sınıf'] = gun_sinif.strip()
                            df.at[idx, '1. Dönem Puanı'] = gun_puan
                            df.at[idx, 'Proje'] = gun_proje
                            df.at[idx, 'Durum'] = gun_durum
                            veriyi_kaydet(df)
                            st.success("✅ Öğrenci bilgileri güncellendi!")
                            st.rerun()

        elif islem == "🗑️ Öğrenci Sil":
            if df.empty:
                st.warning("⚠️ Silinecek öğrenci yok.")
            else:
                ogr_liste_s = df.apply(lambda r: f"{r['Sınıf']} — {r['Okul No']} — {r.get('Öğrenci Adı Soyadı','')}", axis=1).tolist()
                secim_s = st.selectbox("Silinecek Öğrenciyi Seçin:", ["— Seçiniz —"] + ogr_liste_s, key="sil_sec")
                if secim_s != "— Seçiniz —":
                    st.warning(f"⚠️ **'{secim_s}'** kaydını kalıcı olarak silmek istediğinizden emin misiniz?")
                    col_sil = st.columns([1, 1, 2])
                    with col_sil[0]:
                        if st.button("🗑️ Evet, Sil", key="sil_btn"):
                            okul_no_s = secim_s.split(" — ")[1]
                            df = df[df['Okul No'] != okul_no_s].reset_index(drop=True)
                            veriyi_kaydet(df)
                            st.success("✅ Öğrenci silindi.")
                            st.rerun()

    with otab3:
        st.markdown("### 🤖 Puanlama ve Yapay Zeka Değerlendirmesi")

        if df.empty:
            st.warning("⚠️ Önce sisteme öğrenci ekleyin.")
        else:
            ogr_liste_p = df.apply(lambda r: f"{r['Sınıf']} — {r['Okul No']} — {r.get('Öğrenci Adı Soyadı','')}", axis=1).tolist()
            secim_p = st.selectbox("Değerlendirilecek Öğrenci:", ["— Seçiniz —"] + ogr_liste_p, key="puan_sec")

            if secim_p != "— Seçiniz —":
                okul_no_p = secim_p.split(" — ")[1]
                idx = df.index[df['Okul No'] == okul_no_p].tolist()[0]
                bilgi = df.iloc[idx]

                # ---------------------------------------------------------
                # YAPAY ZEKA İŞLEMİNİ WIDGETLAR ÇİZİLMEDEN YAKALAYAN KISIM
                # ---------------------------------------------------------
                if st.session_state.get(f"ai_tetikle_{idx}"):
                    puanlar_dict = {k["id"]: st.session_state.get(f"puan_{idx}_{k['id']}", 0) for k in KRITERLER}
                    ham_metin = st.session_state.get(f"ham_{idx}", "")
                    
                    with st.spinner("🤖 Gemini Yapay Zeka Değerlendirmesi Hazırlanıyor... Lütfen Bekleyin."):
                        try:
                            # Öğretmen adını ve branşını AI'a parametre olarak gönderiyoruz
                            json_data = ai_degerlendirme_yap(bilgi.to_dict(), ham_metin, puanlar_dict, guncel_ad, guncel_brans)
                            if json_data:
                                for k in KRITERLER:
                                    kid = k['id']
                                    if kid in json_data:
                                        st.session_state[f"aciklama_{idx}_{kid}"] = json_data[kid]
                                if "genel" in json_data:
                                    st.session_state[f"genel_{idx}"] = json_data["genel"]
                                st.session_state["ai_durum"] = ("success", "✅ Yapay zeka değerlendirmesi başarıyla tamamlandı! Kutu içerikleri güncellendi.")
                            else:
                                st.session_state["ai_durum"] = ("error", "❌ Yapay zeka metni döndüremedi.")
                        except Exception as e:
                            st.session_state["ai_durum"] = ("error", f"❌ Beklenmedik bir hata oluştu: {e}")
                    
                    st.session_state[f"ai_tetikle_{idx}"] = False

                if "ai_durum" in st.session_state:
                    durum_tip, durum_mesaj = st.session_state.pop("ai_durum")
                    if durum_tip == "success":
                        st.success(durum_mesaj)
                    else:
                        st.error(durum_mesaj)
                # ---------------------------------------------------------

                with st.expander("👁️ Mevcut Karne Önizlemesi", expanded=False):
                    st.markdown(karne_html_olustur(bilgi, guncel_ad, guncel_brans), unsafe_allow_html=True)

                st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
                st.markdown("#### 🎯 Kriter Bazlı Puanlama")
                st.info("💡 Puanları giriniz. '✨ Yapay Zeka ile Değerlendir' butonuna bastığınızda tüm açıklamalar otomatik doldurulacaktır.")

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

                for k in KRITERLER:
                    pk = f"puan_{idx}_{k['id']}"
                    ak = f"aciklama_{idx}_{k['id']}"
                    mevcut_puan = st.session_state[pk]
                    oran_pct = int((mevcut_puan / k['max']) * 100) if k['max'] > 0 else 0
                    renk_bar = puan_renk(mevcut_puan, k['max'])

                    st.markdown(f"""
                    <div class="kriter-box">
                      <div class="kriter-baslik">{k['icon']} {k['baslik']} <span style="color:rgba(255,255,255,0.35); font-weight:400;">(Maks: {k['max']} puan)</span></div>
                      <div class="kriter-aciklama">{k['aciklama']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_puan, c_aciklama = st.columns([1, 4])
                    with c_puan:
                        st.number_input(f"Puan (0-{k['max']})", min_value=0, max_value=k['max'],
                                        key=pk, label_visibility="visible")
                        st.markdown(f"""
                        <div class="puan-bar-wrapper">
                          <div class="puan-bar-fill" style="width:{oran_pct}%; background:linear-gradient(90deg,{renk_bar},{renk_bar}88);"></div>
                        </div>
                        <div style="text-align:right; font-size:0.7rem; color:rgba(255,255,255,0.4); margin-top:2px;">{oran_pct}%</div>
                        """, unsafe_allow_html=True)
                    with c_aciklama:
                        st.text_input("Açıklama (AI doldurur veya manuel yazın)", key=ak, label_visibility="visible")

                    toplam_anlik += st.session_state[pk]

                st.markdown(f"""
                <div style="display:flex; justify-content:center; margin:16px 0;">
                  <div class="toplam-badge">
                    {toplam_anlik} <span style="font-size:1rem; opacity:0.7;">/ 100</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                gk = f"genel_{idx}"
                if gk not in st.session_state:
                    db_g = df.at[idx, 'Genel Değerlendirme Yorumu']
                    st.session_state[gk] = str(db_g) if pd.notna(db_g) else ""

                st.text_area("📝 Genel Değerlendirme Yorumu (AI doldurur veya manuel yazın)",
                             key=gk, height=110)

                st.markdown("---")

                ham_metin = st.text_area(
                    "💬 Öğretmen Notu (Yapay Zekaya Özel Talimat)",
                    placeholder="Örn: 'Ödev çok geç teslim edildi ama araştırma kısmı mükemmeldi.' — Buraya yazdığınız not, yapay zekanın tüm açıklamalarını şekillendirecektir.",
                    height=70,
                    key=f"ham_{idx}"
                )

                col_ai, col_save = st.columns(2)

                with col_ai:
                    st.markdown('<div class="ai-btn">', unsafe_allow_html=True)
                    ai_clicked = st.button("✨  Yapay Zeka ile Tüm Açıklamaları Doldur", use_container_width=True, key="ai_btn")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_save:
                    st.markdown('<div class="kaydet-btn">', unsafe_allow_html=True)
                    save_clicked = st.button("💾  Puanları ve Açıklamaları Kaydet", use_container_width=True, key="save_btn")
                    st.markdown('</div>', unsafe_allow_html=True)

                if ai_clicked:
                    st.session_state[f"ai_tetikle_{idx}"] = True
                    st.rerun()

                if save_clicked:
                    for k in KRITERLER:
                        df.at[idx, f"{k['baslik']} Puanı"] = st.session_state[f"puan_{idx}_{k['id']}"]
                        df.at[idx, f"{k['baslik']} Açıklaması"] = st.session_state[f"aciklama_{idx}_{k['id']}"]
                    df.at[idx, 'Genel Değerlendirme Yorumu'] = st.session_state[gk]
                    toplam = sum(st.session_state[f"puan_{idx}_{k['id']}"] for k in KRITERLER)
                    df.at[idx, 'Toplam Puan'] = toplam
                    veriyi_kaydet(df)
                    st.success(f"✅ {secim_p.split(' — ')[2]} için kayıt başarıyla güncellendi! Toplam Puan: {toplam}/100")

    with otab4:
        st.markdown("### 📊 Raporlama ve Karne Çıktıları")

        if df.empty:
            st.warning("⚠️ Raporlanacak veri bulunmuyor.")
        else:
            mevcut_siniflar = sorted(df['Sınıf'].dropna().unique().tolist())

            col_filtre, col_sinif = st.columns([1, 2])
            with col_filtre:
                # SEÇİLİ ÖĞRENCİLER BUTONU EKLENDİ
                filtre = st.radio("Görünüm:", ["🏫 Tüm Sınıflar", "📋 Tek Sınıf", "👤 Seçili Öğrenciler"], horizontal=True)
            
            with col_sinif:
                if filtre == "📋 Tek Sınıf":
                    secili_sinif = st.selectbox("Sınıf Seçin:", mevcut_siniflar)
                    gosterilecek_df = df[df['Sınıf'] == secili_sinif]
                    dosya_adi = f"{secili_sinif.replace('/', '_')}_Rapor.xlsx"
                
                elif filtre == "👤 Seçili Öğrenciler":
                    secili_sinif = st.selectbox("Sınıf Seçin:", mevcut_siniflar)
                    # Sınıftaki öğrencileri çoklu seçim kutusunda listeliyoruz
                    sinif_ogrencileri = df[df['Sınıf'] == secili_sinif].apply(lambda x: f"{x['Okul No']} - {x['Öğrenci Adı Soyadı']}", axis=1).tolist()
                    secilen_isimler = st.multiselect("PDF'i Çıkarılacak Öğrencileri Seçin (Birden fazla seçebilirsiniz):", sinif_ogrencileri)
                    
                    if secilen_isimler:
                        # Seçilen isimlerin okul numaralarını ayırıp filtreliyoruz
                        secilen_nolar = [isim.split(" - ")[0] for isim in secilen_isimler]
                        gosterilecek_df = df[(df['Sınıf'] == secili_sinif) & (df['Okul No'].isin(secilen_nolar))]
                        dosya_adi = f"Secili_Ogrenciler_Rapor.xlsx"
                    else:
                        # Henüz bir şey seçilmediyse boş bir liste döndürüyoruz
                        gosterilecek_df = pd.DataFrame(columns=df.columns)
                        dosya_adi = "Rapor.xlsx"

                else:
                    gosterilecek_df = df
                    secili_sinif = None
                    dosya_adi = "Tum_Siniflar_Rapor.xlsx"

            if not gosterilecek_df.empty or filtre == "🏫 Tüm Sınıflar":
                goster_cols = ['Sınıf', 'Okul No', 'Öğrenci Adı Soyadı'] + [f"{k['baslik']} Puanı" for k in KRITERLER] + ['Toplam Puan']
                temiz_df = gosterilecek_df[[c for c in goster_cols if c in gosterilecek_df.columns]].copy()

                for k in KRITERLER:
                    col_name = f"{k['baslik']} Puanı"
                    if col_name in temiz_df.columns:
                        temiz_df[col_name] = pd.to_numeric(temiz_df[col_name], errors='coerce')
                if 'Toplam Puan' in temiz_df.columns:
                    temiz_df['Toplam Puan'] = pd.to_numeric(temiz_df['Toplam Puan'], errors='coerce')

                st.dataframe(temiz_df, use_container_width=True, hide_index=True)

                st.markdown("#### 📥 İndirme Seçenekleri")
                dl1, dl2, dl3 = st.columns(3)

                with dl1:
                    out1 = io.BytesIO()
                    with pd.ExcelWriter(out1, engine='xlsxwriter') as w:
                        gosterilecek_df.to_excel(w, index=False, sheet_name='Rapor')
                    st.download_button("📊  Seçili Excel'i İndir", data=out1.getvalue(),
                                       file_name=dosya_adi, use_container_width=True,
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                with dl2:
                    out2 = io.BytesIO()
                    with pd.ExcelWriter(out2, engine='xlsxwriter') as w:
                        for s in mevcut_siniflar:
                            sinif_df = df[df['Sınıf'] == s]
                            sinif_df.to_excel(w, index=False, sheet_name=s.replace('/', '_'))
                    st.download_button("📑  Tüm Sınıflar (Ayrı Sayfalar)", data=out2.getvalue(),
                                       file_name="Tum_Siniflar.xlsx", use_container_width=True,
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                with dl3:
                    if filtre in ["📋 Tek Sınıf", "👤 Seçili Öğrenciler"]:
                        if not gosterilecek_df.empty:
                            html_karne = toplu_karne_html_dosyasi_uret(gosterilecek_df, guncel_ad, guncel_brans)
                            st.download_button(
                                "🖨️  Karneleri PDF Olarak İndir",
                                data=html_karne,
                                file_name=f"{'Secili_Ogrenciler' if filtre == '👤 Seçili Öğrenciler' else secili_sinif.replace('/', '_')}_Karneler.html",
                                mime="text/html",
                                use_container_width=True,
                                help="İndirilen HTML dosyasını tarayıcıda açın → Ctrl+P → PDF olarak kaydet → WhatsApp'tan velilere gönderin."
                            )
                        else:
                            st.warning("İndirilecek öğrenci seçilmedi.")
                    else:
                        st.info("💡 Karne çıktısı için 'Tek Sınıf' veya 'Seçili Öğrenciler' görünümünü seçin.")

                if filtre == "🏫 Tüm Sınıflar" and not df.empty:
                    st.markdown("---")
                    st.markdown("#### 📈 Sınıf Bazlı Ortalama Puanlar")
                    ort_df = df.groupby('Sınıf')['Toplam Puan'].apply(lambda x: pd.to_numeric(x, errors='coerce').mean()).reset_index()
                    ort_df.columns = ['Sınıf', 'Ortalama']
                    ort_df = ort_df.dropna().sort_values('Sınıf')
                    if not ort_df.empty:
                        st.bar_chart(ort_df.set_index('Sınıf'))

    # YENİ AYARLAR SEKMESİ
    with otab5:
        st.markdown("### ⚙️ Öğretmen Ayarları & Profil")
        st.info("Sistemi kullanan öğretmenin adını ve branşını buradan değiştirebilirsiniz. Bu bilgiler karnelerin altına imza olarak eklenecek ve yapay zeka tarafından kullanılacaktır.")
        
        st.markdown('<div class="glass-card" style="padding:20px; max-width:600px;">', unsafe_allow_html=True)
        yeni_ad = st.text_input("Öğretmen Adı Soyadı:", value=st.session_state["ogretmen_adi"])
        yeni_brans = st.text_input("Branş (Örn: Fen Bilimleri, Türkçe vs.):", value=st.session_state["ogretmen_bransi"])
        
        if st.button("💾 Bilgileri Güncelle", type="primary"):
            st.session_state["ogretmen_adi"] = yeni_ad.strip()
            st.session_state["ogretmen_bransi"] = yeni_brans.strip()
            st.success("✅ Öğretmen bilgileri başarıyla güncellendi! Karneler ve yapay zeka artık bu bilgilere göre ayarlandı.")
            time.sleep(1)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# ANA ÇALIŞTIRMA
# ==========================================

def main():
    st.markdown("""
    <div class="hero-header">
      <div class="hero-title">🏫 Gazi Ortaokulu</div>
      <div class="hero-subtitle">Proje Değerlendirme Sistemi · 2025-2026 Eğitim Öğretim Yılı</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎓 Öğrenci Girişi", "👨‍🏫 Öğretmen Paneli"])
    df = veri_yukle()

    with tab1:
        ogrenci_paneli(df)
    with tab2:
        ogretmen_paneli(df)

if __name__ == "__main__":
    main()
