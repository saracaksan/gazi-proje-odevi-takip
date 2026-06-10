import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import json
import time

# ==========================================
# SAYFA YAPILANDIRMASI
# ==========================================
st.set_page_config(
    page_title="Gazi Ortaokulu | Proje Değerlendirme",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── ÖZEL CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2044 100%);
    min-height: 100vh;
}

/* ── HERO ── */
.hero-header {
    background: linear-gradient(135deg, #1e40af, #3b82f6, #60a5fa);
    border-radius: 20px; padding: 32px 40px; margin-bottom: 28px;
    text-align: center; box-shadow: 0 20px 60px rgba(59,130,246,0.4);
    position: relative; overflow: hidden;
}
.hero-header::before {
    content:''; position:absolute; top:-50%; left:-50%;
    width:200%; height:200%;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
    animation: shimmer 6s infinite linear;
}
@keyframes shimmer { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }
.hero-title {
    font-family:'Nunito',sans-serif; font-size:2.4rem; font-weight:900;
    color:white; margin:0 0 6px 0; text-shadow:0 2px 10px rgba(0,0,0,0.3);
    letter-spacing:-0.5px; position:relative; z-index:1;
}
.hero-subtitle {
    font-size:1rem; color:rgba(255,255,255,0.85);
    margin:0; font-weight:500; position:relative; z-index:1;
}

/* ── TABS ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background:rgba(255,255,255,0.05); border-radius:16px;
    padding:6px; border:1px solid rgba(255,255,255,0.1); gap:4px; margin-bottom:20px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background:transparent; border-radius:12px;
    color:rgba(255,255,255,0.6) !important; font-weight:600;
    font-size:0.95rem; padding:10px 24px; border:none; transition:all 0.25s;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background:rgba(255,255,255,0.08); color:white !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background:linear-gradient(135deg,#2563eb,#3b82f6) !important;
    color:white !important; box-shadow:0 4px 16px rgba(37,99,235,0.5);
}

/* ── KARTLAR ── */
.glass-card {
    background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12);
    border-radius:18px; padding:24px; margin-bottom:18px; backdrop-filter:blur(12px);
}
.metric-card {
    background:linear-gradient(135deg,rgba(37,99,235,0.3),rgba(59,130,246,0.15));
    border:1px solid rgba(96,165,250,0.3); border-radius:16px;
    padding:20px; text-align:center;
}
.metric-card .val {
    font-family:'Nunito',sans-serif; font-size:2.2rem; font-weight:900;
    color:#60a5fa; line-height:1;
}
.metric-card .lbl {
    font-size:0.75rem; color:rgba(255,255,255,0.5);
    margin-top:6px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;
}

/* ── INPUTS – tüm input/select/textarea ── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stNumberInput > div > div > input {
    background:rgba(255,255,255,0.08) !important;
    border:1px solid rgba(255,255,255,0.18) !important;
    border-radius:10px !important; color:white !important;
    caret-color:white;
}
.stTextInput > div > div > input::placeholder,
.stTextArea  > div > div > textarea::placeholder {
    color:rgba(255,255,255,0.35) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color:#3b82f6 !important;
    box-shadow:0 0 0 3px rgba(59,130,246,0.2) !important;
}

/* ── SELECTBOX – hem kutu hem dropdown ── */
[data-baseweb="select"] > div {
    background:rgba(255,255,255,0.08) !important;
    border:1px solid rgba(255,255,255,0.18) !important;
    border-radius:10px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color:white !important;
}
[data-baseweb="popover"] {
    background:#1e293b !important;
    border:1px solid rgba(255,255,255,0.15) !important;
    border-radius:12px !important;
}
[data-baseweb="menu"] li {
    color:white !important; background:transparent !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] {
    background:rgba(59,130,246,0.25) !important;
}
/* SVG ok ikonu beyaz */
[data-baseweb="select"] svg { fill:white !important; }

/* ── LABELS ── */
label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label,
.stRadio label, [data-testid="stWidgetLabel"] {
    color:rgba(255,255,255,0.8) !important;
    font-weight:600 !important; font-size:0.85rem !important;
}

/* ── BUTONLAR ── */
.stButton > button {
    background:linear-gradient(135deg,#2563eb,#3b82f6) !important;
    color:white !important; border:none !important; border-radius:12px !important;
    padding:12px 24px !important; font-weight:700 !important;
    font-family:'Nunito',sans-serif !important; font-size:0.95rem !important;
    transition:all 0.25s !important; box-shadow:0 4px 16px rgba(37,99,235,0.4) !important;
}
.stButton > button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 8px 24px rgba(37,99,235,0.6) !important;
}
.stDownloadButton > button {
    background:linear-gradient(135deg,#059669,#10b981) !important;
    color:white !important; border:none !important; border-radius:12px !important;
    font-weight:700 !important; box-shadow:0 4px 16px rgba(5,150,105,0.4) !important;
    transition:all 0.25s !important;
}
.stDownloadButton > button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 8px 24px rgba(5,150,105,0.6) !important;
}
.ai-btn > div > button {
    background:linear-gradient(135deg,#7c3aed,#a855f7) !important;
    box-shadow:0 4px 20px rgba(124,58,237,0.5) !important;
}
.ai-btn > div > button:hover {
    box-shadow:0 8px 28px rgba(124,58,237,0.7) !important;
}
.kaydet-btn > div > button {
    background:linear-gradient(135deg,#059669,#10b981) !important;
    box-shadow:0 4px 20px rgba(5,150,105,0.5) !important;
}

/* ── MESAJ KUTULARI ── */
[data-testid="stSuccess"] { background:rgba(16,185,129,0.15) !important; border:1px solid rgba(16,185,129,0.3) !important; border-radius:12px !important; }
[data-testid="stError"]   { background:rgba(239,68,68,0.15)  !important; border:1px solid rgba(239,68,68,0.3)  !important; border-radius:12px !important; }
[data-testid="stWarning"] { background:rgba(245,158,11,0.15) !important; border:1px solid rgba(245,158,11,0.3) !important; border-radius:12px !important; }
[data-testid="stInfo"]    { background:rgba(59,130,246,0.15) !important; border:1px solid rgba(59,130,246,0.3)  !important; border-radius:12px !important; }

/* ── TABLO ── */
[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; }

/* ── NUMBER INPUT okları ── */
.stNumberInput button {
    background:rgba(255,255,255,0.1) !important; border:none !important;
    color:white !important; border-radius:6px !important;
}

/* ── FORM ── */
[data-testid="stForm"] {
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
    border-radius:16px; padding:20px;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:14px !important;
}
[data-testid="stExpanderToggleIcon"] { color:white !important; }

/* ── RADIO ── */
.stRadio > div { gap:12px; }
[data-testid="stRadio"] label {
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    border-radius:10px !important; padding:8px 16px !important;
    transition:all 0.2s !important;
}
[data-testid="stRadio"] label:hover {
    background:rgba(59,130,246,0.15) !important;
}

/* ── KRITER KUTUSU ── */
.kriter-box {
    background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);
    border-radius:14px; padding:16px 20px; margin-bottom:14px; transition:border-color 0.2s;
}
.kriter-box:hover { border-color:rgba(59,130,246,0.4); }
.kriter-baslik {
    font-family:'Nunito',sans-serif; font-weight:800;
    color:#93c5fd; font-size:0.95rem; margin-bottom:2px;
}
.kriter-aciklama {
    color:rgba(255,255,255,0.4); font-size:0.78rem; font-style:italic;
}

/* ── PUAN BAR ── */
.puan-bar-wrapper {
    width:100%; height:7px; background:rgba(255,255,255,0.1);
    border-radius:10px; overflow:hidden; margin-top:5px;
}
.puan-bar-fill { height:100%; border-radius:10px; transition:width 0.5s ease; }

/* ── TOPLAM PUAN BADGE ── */
.toplam-badge {
    background:linear-gradient(135deg,#1e40af,#2563eb);
    color:white; font-family:'Nunito',sans-serif;
    font-size:1.8rem; font-weight:900; border-radius:16px;
    padding:16px 40px; text-align:center;
    box-shadow:0 8px 24px rgba(37,99,235,0.4);
    display:inline-block; border:1px solid rgba(96,165,250,0.3);
}

/* ── ŞİFRE EKRANI ── */
.sifre-card {
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12);
    border-radius:20px; padding:48px; max-width:440px;
    margin:60px auto; text-align:center; backdrop-filter:blur(12px);
}

/* ── CUSTOM DIVIDER ── */
.custom-divider {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent);
    margin:20px 0;
}

/* ── METİNLER ── */
p, span, div, li { color:rgba(255,255,255,0.85); }
h1,h2,h3,h4 { color:white; font-family:'Nunito',sans-serif; font-weight:800; }
strong { color:white; }
em { color:rgba(255,255,255,0.7); }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:rgba(255,255,255,0.05); }
::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.2); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# GEMİNİ YAPILANDIRMASI
# ==========================================
GEMINI_API_KEY = "AIzaSyDR59-y8bOekDJBHjSN9vvFfjhWXQfPRUM"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# SABİTLER VE VERİTABANI
# ==========================================
DATA_FILE = "veritabani.csv"

KRITERLER = [
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu",  "max": 40, "icon": "📚",
     "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi ve konu hakimiyeti."},
    {"id": "k2", "baslik": "Düzen ve Tertip",             "max": 15, "icon": "📐",
     "aciklama": "Ödevin temiz, okunaklı ve düzenli hazırlanmış olması."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍",
     "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler veya açıklamalar."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum",        "max": 15, "icon": "🎨",
     "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi."},
    {"id": "k5", "baslik": "Zamanında Teslim",            "max": 15, "icon": "⏰",
     "aciklama": "Projenin belirtilen tarihte (26 Nisan 2026) teslim edilmesi."},
]

GEREKLI_SUTUNLAR = ['S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf',
                    '1. Dönem Puanı', 'Proje', 'Durum']
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
    sablon_df = pd.DataFrame(columns=[
        'S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf',
        '1. Dönem Puanı', 'Proje', 'Durum'
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Sablonu')
        ws = writer.sheets['Ogrenci_Sablonu']
        for i in range(len(sablon_df.columns)):
            ws.set_column(i, i, 22)
    return output.getvalue()


def puan_renk(puan, max_puan):
    oran = puan / max_puan if max_puan > 0 else 0
    if oran >= 0.85: return "#10b981"
    elif oran >= 0.60: return "#f59e0b"
    return "#ef4444"


def karne_html_olustur(bilgi):
    toplam = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
    toplam = 0 if pd.isna(toplam) else int(toplam)
    renk = puan_renk(toplam, 100)

    html = f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;background:white;border-radius:16px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.15);">
  <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);padding:22px 28px;color:white;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <div>
        <div style="font-size:10px;opacity:0.7;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Gazi Ortaokulu · Matematik Birimi</div>
        <div style="font-size:1.35rem;font-weight:800;">Proje Değerlendirme Karnesi</div>
      </div>
      <div style="background:white;border-radius:12px;padding:10px 20px;text-align:center;">
        <div style="font-size:2rem;font-weight:900;color:{renk};line-height:1;">{toplam}</div>
        <div style="font-size:0.65rem;color:#64748b;margin-top:2px;">/ 100 PUAN</div>
      </div>
    </div>
  </div>
  <div style="background:#f8fafc;padding:14px 28px;border-bottom:2px solid #e2e8f0;display:flex;gap:28px;flex-wrap:wrap;">
    <div><span style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;">👤 Öğrenci</span><br><span style="color:#1e293b;font-weight:700;">{bilgi.get('Öğrenci Adı Soyadı','')}</span></div>
    <div><span style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;">🏫 Sınıf</span><br><span style="color:#1e293b;font-weight:700;">{bilgi.get('Sınıf','')}</span></div>
    <div><span style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;">🔢 No</span><br><span style="color:#1e293b;font-weight:700;">{bilgi.get('Okul No','')}</span></div>
    <div><span style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;">📖 Proje</span><br><span style="color:#1e293b;font-weight:700;">{bilgi.get('Proje','-')}</span></div>
    <div><span style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;">📅 1. Dönem</span><br><span style="color:#1e293b;font-weight:700;">{bilgi.get('1. Dönem Puanı','-')}</span></div>
  </div>
  <div style="padding:0 12px 8px;">
    <table style="width:100%;border-collapse:collapse;margin-top:10px;">
      <tr style="background:#f1f5f9;">
        <th style="padding:10px 12px;text-align:left;font-size:0.73rem;color:#475569;font-weight:700;text-transform:uppercase;width:27%;">Kriter</th>
        <th style="padding:10px 12px;text-align:center;font-size:0.73rem;color:#475569;font-weight:700;text-transform:uppercase;width:8%;">Max</th>
        <th style="padding:10px 12px;text-align:center;font-size:0.73rem;color:#475569;font-weight:700;text-transform:uppercase;width:10%;">Alınan</th>
        <th style="padding:10px 12px;text-align:left;font-size:0.73rem;color:#475569;font-weight:700;text-transform:uppercase;">Değerlendirme</th>
      </tr>"""

    for i, k in enumerate(KRITERLER):
        puan = pd.to_numeric(bilgi.get(f"{k['baslik']} Puanı", 0), errors='coerce')
        puan = 0 if pd.isna(puan) else int(puan)
        aciklama = bilgi.get(f"{k['baslik']} Açıklaması", "")
        aciklama = "Henüz değerlendirme girilmedi." if (pd.isna(aciklama) or str(aciklama).strip() == "") else str(aciklama)
        r = puan_renk(puan, k['max'])
        oran_pct = int((puan / k['max']) * 100) if k['max'] > 0 else 0
        bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
        html += f"""
      <tr style="background:{bg};border-bottom:1px solid #e2e8f0;">
        <td style="padding:11px 12px;">
          <div style="font-weight:700;color:#1e293b;font-size:0.87rem;">{k['icon']} {k['baslik']}</div>
          <div style="font-size:0.7rem;color:#94a3b8;margin-top:2px;">{k['aciklama']}</div>
        </td>
        <td style="padding:11px 12px;text-align:center;color:#475569;font-weight:600;">{k['max']}</td>
        <td style="padding:11px 12px;text-align:center;">
          <span style="color:{r};font-size:1.25rem;font-weight:900;">{puan}</span>
          <div style="width:100%;height:4px;background:#e2e8f0;border-radius:4px;margin-top:4px;overflow:hidden;">
            <div style="width:{oran_pct}%;height:100%;background:{r};border-radius:4px;"></div>
          </div>
        </td>
        <td style="padding:11px 12px;color:#166534;font-size:0.84rem;font-style:italic;line-height:1.5;">{aciklama}</td>
      </tr>"""

    genel = bilgi.get('Genel Değerlendirme Yorumu', '')
    genel = "Henüz genel değerlendirme yapılmadı." if (pd.isna(genel) or str(genel).strip() == "") else str(genel)

    html += f"""
    </table>
  </div>
  <div style="margin:10px 12px 14px;background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 12px 12px 0;padding:13px 16px;">
    <div style="font-size:0.72rem;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:5px;">💬 Genel Değerlendirme</div>
    <div style="color:#1e40af;font-size:0.88rem;line-height:1.6;">{genel}</div>
  </div>
  <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:12px 28px;display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:0.75rem;color:#94a3b8;">Gazi Ortaokulu · Matematik · 2025-2026</div>
    <div style="text-align:right;">
      <div style="font-weight:700;color:#1e293b;font-size:0.85rem;">Sıraç AKSAN</div>
      <div style="font-size:0.7rem;color:#94a3b8;">Matematik Öğretmeni</div>
    </div>
  </div>
</div>"""
    return html


def toplu_karne_html_dosyasi_uret(df_sinif):
    html = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Proje Karneleri – Gazi Ortaokulu</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',sans-serif;background:#f1f5f9}
  .page{background:white;width:210mm;margin:10mm auto;padding:12mm 14mm;border-radius:4px;box-shadow:0 4px 20px rgba(0,0,0,0.08);page-break-after:always}
  table{width:100%;border-collapse:collapse}
  th{background:#1e3a8a;color:white;padding:8px 11px;font-size:0.7rem;text-align:left}
  td{padding:8px 11px;font-size:0.8rem;border-bottom:1px solid #e2e8f0;vertical-align:top}
  tr:nth-child(even) td{background:#f8fafc}
  .header{background:linear-gradient(135deg,#1e3a8a,#2563eb);color:white;padding:14px 18px;border-radius:8px;margin-bottom:12px}
  .bilgi{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px;font-size:0.82rem}
  .yorum{background:#eff6ff;border-left:3px solid #3b82f6;padding:9px 13px;margin-top:8px;font-size:0.8rem;color:#1e40af;border-radius:0 8px 8px 0}
  .imza{margin-top:16px;text-align:right;font-size:0.78rem;color:#475569;border-top:1px solid #e2e8f0;padding-top:8px}
  @media print{body{background:white}.page{box-shadow:none;margin:0;border-radius:0;width:100%}}
</style>
</head>
<body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam = pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce')
        toplam = 0 if pd.isna(toplam) else int(toplam)
        renk = puan_renk(toplam, 100)

        html += f"""
<div class="page">
  <div class="header">
    <div style="font-size:0.65rem;opacity:0.7;letter-spacing:2px;text-transform:uppercase;margin-bottom:3px;">Gazi Ortaokulu · Matematik Birimi · 2025-2026</div>
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div style="font-size:1.1rem;font-weight:800;">Proje Değerlendirme Karnesi</div>
      <div style="background:white;color:{renk};font-size:1.6rem;font-weight:900;padding:4px 14px;border-radius:8px;">{toplam}<span style="font-size:0.7rem;color:#64748b;">/100</span></div>
    </div>
  </div>
  <div class="bilgi">
    <span><b>👤</b> {b.get('Öğrenci Adı Soyadı','')}</span>
    <span><b>🏫</b> {b.get('Sınıf','')}</span>
    <span><b>🔢</b> {b.get('Okul No','')}</span>
    <span><b>📖</b> {b.get('Proje','-')}</span>
    <span><b>1. Dönem:</b> {b.get('1. Dönem Puanı','-')}</span>
  </div>
  <table>
    <tr><th>Kriter</th><th style="width:50px;text-align:center;">Max</th><th style="width:60px;text-align:center;">Alınan</th><th>Değerlendirme</th></tr>"""

        for k in KRITERLER:
            p = pd.to_numeric(b.get(f"{k['baslik']} Puanı", 0), errors='coerce')
            p = 0 if pd.isna(p) else int(p)
            a = b.get(f"{k['baslik']} Açıklaması", "")
            a = "-" if (pd.isna(a) or str(a).strip() == "") else str(a)
            r = puan_renk(p, k['max'])
            html += f"<tr><td><b>{k['icon']} {k['baslik']}</b><br><span style='font-size:0.67rem;color:#94a3b8;'>{k['aciklama']}</span></td><td style='text-align:center;color:#475569;font-weight:600;'>{k['max']}</td><td style='text-align:center;color:{r};font-size:1rem;font-weight:900;'>{p}</td><td style='color:#166534;font-style:italic;'>{a}</td></tr>"

        genel = b.get('Genel Değerlendirme Yorumu', '')
        genel = "-" if (pd.isna(genel) or str(genel).strip() == "") else str(genel)
        html += f"""
  </table>
  <div class="yorum"><b>💬 Genel Değerlendirme:</b> {genel}</div>
  <div class="imza"><b>Sıraç AKSAN</b> · Matematik Öğretmeni</div>
</div>"""

    html += "\n</body></html>"
    return html


# ==========================================
# GEMİNİ AI DEĞERLENDİRME FONKSİYONU
# ==========================================
def ai_degerlendirme_yap(bilgi_dict: dict, ham_metin: str, puanlar: dict) -> dict:
    """Gemini API ile kriter açıklamaları ve genel yorum üretir."""

    puan_ozeti = "\n".join([
        f"  - {k['icon']} {k['baslik']} ({k['max']} üzerinden): {puanlar.get(k['id'], 0)} puan"
        for k in KRITERLER
    ])

    ogrenci_adi = bilgi_dict.get('Öğrenci Adı Soyadı', 'Öğrenci')
    sinif        = bilgi_dict.get('Sınıf', '')
    proje_konu   = bilgi_dict.get('Proje', '')
    d1_puan      = bilgi_dict.get('1. Dönem Puanı', '')
    durum        = bilgi_dict.get('Durum', '')
    toplam       = sum(puanlar.values())

    not_kismi = ham_metin.strip() if ham_metin.strip() else \
        "Öğretmen ek notu yok; sadece yukarıdaki puanlara ve öğrenci bilgilerine göre değerlendir."

    prompt = f"""Sen Gazi Ortaokulu'nda görev yapan deneyimli, anlayışlı ve motive edici bir matematik öğretmenisin.

📋 ÖĞRENCİ BİLGİLERİ:
  • Ad Soyad   : {ogrenci_adi}
  • Sınıf      : {sinif}
  • Proje Konu : {proje_konu}
  • 1. Dönem   : {d1_puan}
  • Durum      : {durum}

📊 PROJE PUANLARI (Toplam: {toplam}/100):
{puan_ozeti}

📝 ÖĞRETMEN NOTU:
{not_kismi}

🎯 GÖREVLER:
1) Her kriter için öğrenciye doğrudan "sen" diliyle hitap eden, 1-2 cümlelik ÖZGÜN ve YAPICI bir değerlendirme yaz.
   • Tam/yüksek puan (≥%85): Samimi tebrik + bu başarıyı neye bağlıyorsun?
   • Orta puan (%60-84): Güçlü yönü öne çıkar + nazikçe gelişim önerisi.
   • Düşük puan (<%60): Asla cesaretini kırma; eksikliği şefkatle ifade et + nasıl düzeltir?
   • Öğretmen notu varsa mutlaka dikkate al.

2) "genel" kısmında:
   - Önce matematiğin / analitik düşüncenin günlük hayattaki önemine kısa değin.
   - Ardından {ogrenci_adi} adını kullanarak projenin genel değerlendirmesini yap.
   - Güçlü ve geliştirilecek yönlere değin.
   - Motive edici, sıcak bir kapanış cümlesi ekle.

⚠️ KURALLAR:
- Türkçe yaz. Klişelerden kaçın. Her metin özgün olsun.
- Başka hiçbir şey ekleme; SADECE aşağıdaki JSON formatını döndür:

{{
  "k1": "İçerik ve Bilgi Doğruluğu açıklaması",
  "k2": "Düzen ve Tertip açıklaması",
  "k3": "Araştırma ve Zenginleştirme açıklaması",
  "k4": "Yaratıcılık ve Sunum açıklaması",
  "k5": "Zamanında Teslim açıklaması",
  "genel": "Genel motivasyon yorumu"
}}"""

    response = gemini_model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    raw = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(raw)


# ==========================================
# ÖĞRENCİ PANELİ
# ==========================================
def ogrenci_paneli(df):
    st.markdown("""
    <div style="text-align:center;margin-bottom:28px;">
      <div style="font-size:3.2rem;margin-bottom:8px;">🎓</div>
      <div style="font-size:1.5rem;font-weight:800;color:white;font-family:'Nunito',sans-serif;">Proje Sonuç Sorgulama</div>
      <div style="color:rgba(255,255,255,0.5);font-size:0.88rem;margin-top:4px;">
        Sınıfınızı seçin ve okul numaranızı girerek proje karnenize ulaşın
      </div>
    </div>""", unsafe_allow_html=True)

    if df.empty or len(df.columns) < 10:
        st.warning("⚠️ Sisteme henüz veri yüklenmemiştir. Öğretmeninizle iletişime geçin.")
        return

    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        sinif_listesi = ["— Sınıfınızı Seçin —"] + sorted(df['Sınıf'].dropna().unique().tolist())
        sinif = st.selectbox("🏫 Sınıf", sinif_listesi, key="ogr_sinif")
        okul_no = st.text_input("🔢 Okul Numaranız", placeholder="Örnek: 1234", key="ogr_no")
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            sorgula = st.button("🔍  Sonucumu Göster", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if sorgula:
        if sinif == "— Sınıfınızı Seçin —" or not okul_no.strip():
            st.error("❌ Lütfen sınıfınızı seçin ve okul numaranızı girin.")
            return
        ogrenci = df[(df['Sınıf'] == sinif) & (df['Okul No'] == okul_no.strip())]
        if ogrenci.empty:
            st.error("❌ Bu bilgilere ait kayıt bulunamadı. Numaranızı kontrol edin.")
            return

        bilgi = ogrenci.iloc[0]
        toplam = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
        toplam = 0 if pd.isna(toplam) else int(toplam)

        st.success(f"✅ Hoş geldiniz, **{bilgi.get('Öğrenci Adı Soyadı', '')}**!")
        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        renk_val = puan_renk(toplam, 100)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="val" style="color:{renk_val};">{toplam}</div><div class="lbl">Toplam Puan</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="val" style="font-size:1.4rem;">{bilgi.get("Sınıf","")}</div><div class="lbl">Sınıf</div></div>', unsafe_allow_html=True)
        with m3:
            d1 = bilgi.get('1. Dönem Puanı', '-')
            st.markdown(f'<div class="metric-card"><div class="val" style="font-size:1.4rem;">{d1}</div><div class="lbl">1. Dönem Puanı</div></div>', unsafe_allow_html=True)
        with m4:
            dur = bilgi.get('Durum', '-')
            st.markdown(f'<div class="metric-card"><div class="val" style="font-size:1rem;">{dur}</div><div class="lbl">Proje Durumu</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(karne_html_olustur(bilgi), unsafe_allow_html=True)


# ==========================================
# ÖĞRETMEN PANELİ
# ==========================================
def ogretmen_paneli(df):
    if "ogr_giris" not in st.session_state:
        st.session_state["ogr_giris"] = False

    if not st.session_state["ogr_giris"]:
        _, col_m, _ = st.columns([1, 1.2, 1])
        with col_m:
            st.markdown("""
            <div style="text-align:center;margin-bottom:28px;margin-top:20px;">
              <div style="font-size:2.8rem;margin-bottom:8px;">🔐</div>
              <div style="font-size:1.35rem;font-weight:800;color:white;font-family:'Nunito',sans-serif;">Yönetici Paneli</div>
              <div style="color:rgba(255,255,255,0.45);font-size:0.84rem;margin-top:5px;">Devam etmek için şifrenizi girin</div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="glass-card" style="padding:32px;">', unsafe_allow_html=True)
            sifre = st.text_input("Yönetici Şifresi", type="password", placeholder="••••••••", key="admin_pw")
            _, bb, _ = st.columns([1, 2, 1])
            with bb:
                if st.button("🚀  Giriş Yap", use_container_width=True):
                    if sifre == "Sarac.47":
                        st.session_state["ogr_giris"] = True
                        st.rerun()
                    elif sifre:
                        st.error("❌ Hatalı şifre!")
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── GİRİŞ BAŞARILI ──────────────────────────────────────────
    col_hosgeldin, col_cikis = st.columns([5, 1])
    with col_hosgeldin:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);
             border-radius:14px;padding:13px 20px;margin-bottom:18px;display:flex;align-items:center;gap:14px;">
          <span style="font-size:1.6rem;">👋</span>
          <div>
            <div style="font-weight:700;color:#6ee7b7;font-family:'Nunito',sans-serif;">Hoş Geldiniz, Sıraç Hocam!</div>
            <div style="color:rgba(255,255,255,0.45);font-size:0.8rem;">Gazi Ortaokulu · Matematik Proje Yönetimi · 2025-2026</div>
          </div>
        </div>""", unsafe_allow_html=True)
    with col_cikis:
        if st.button("🚪 Çıkış", key="logout"):
            st.session_state["ogr_giris"] = False
            st.rerun()

    t1, t2, t3, t4 = st.tabs([
        "📂 Veri Yükleme",
        "👤 Öğrenci İşlemleri",
        "🤖 Puanlama & Yapay Zeka",
        "📊 Rapor & Karne"
    ])

    # ─── SEKME 1 ─────────────────────────────────────────────────
    with t1:
        st.markdown("### 📥 Şablon ve Veri Yükleme")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("#### ⬇️ Boş Şablon İndir")
            st.markdown('<p style="color:rgba(255,255,255,0.45);font-size:0.84rem;">Şablonu indirin, doldurun ve sisteme yükleyin.</p>', unsafe_allow_html=True)
            st.download_button(
                "📄  Excel Şablonunu İndir", data=bos_sablon_olustur(),
                file_name="Ogrenci_Veri_Sablonu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("#### 📤 Doldurulmuş Dosyayı Yükle")
            st.markdown('<p style="color:rgba(255,255,255,0.45);font-size:0.84rem;">Yalnızca yeni öğrenciler eklenir; mevcut kayıtlar korunur.</p>', unsafe_allow_html=True)
            yuklenen = st.file_uploader("Dosya seçin (.xlsx / .csv)", type=['xlsx', 'csv'], label_visibility="collapsed")
            if yuklenen:
                if st.button("💾  Kaydet", use_container_width=True, key="bulk_save"):
                    try:
                        yeni_df = (pd.read_csv(yuklenen, dtype={"Okul No": str})
                                   if yuklenen.name.endswith('.csv')
                                   else pd.read_excel(yuklenen, dtype={"Okul No": str}))
                        yeni_df['Okul No'] = yeni_df['Okul No'].astype(str).str.strip().str.replace('.0','',regex=False)
                        yeni_df.dropna(subset=['Okul No'], inplace=True)
                        eklenecek = yeni_df[~yeni_df['Okul No'].isin(df['Okul No'].tolist())]
                        if eklenecek.empty:
                            st.warning("⚠️ Tüm öğrenciler zaten kayıtlı!")
                        else:
                            eklenecek = eklenecek.copy()
                            for s in GEREKLI_SUTUNLAR:
                                if s not in eklenecek.columns:
                                    eklenecek[s] = None
                            df_yeni = pd.concat([df, eklenecek], ignore_index=True)
                            veriyi_kaydet(df_yeni)
                            st.success(f"✅ {len(eklenecek)} yeni öğrenci eklendi!")
                            time.sleep(0.6); st.rerun()
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        if not df.empty:
            st.markdown("---")
            st.markdown("#### 📈 Genel İstatistikler")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f'<div class="metric-card"><div class="val">{len(df)}</div><div class="lbl">Toplam Öğrenci</div></div>', unsafe_allow_html=True)
            with s2:
                deg = int(df['Toplam Puan'].notna().sum())
                st.markdown(f'<div class="metric-card"><div class="val">{deg}</div><div class="lbl">Değerlendirilen</div></div>', unsafe_allow_html=True)
            with s3:
                st.markdown(f'<div class="metric-card"><div class="val">{df["Sınıf"].nunique()}</div><div class="lbl">Sınıf Sayısı</div></div>', unsafe_allow_html=True)
            with s4:
                ort = pd.to_numeric(df['Toplam Puan'], errors='coerce').mean()
                ort_str = f"{ort:.1f}" if not pd.isna(ort) else "—"
                st.markdown(f'<div class="metric-card"><div class="val">{ort_str}</div><div class="lbl">Genel Ortalama</div></div>', unsafe_allow_html=True)

    # ─── SEKME 2 ─────────────────────────────────────────────────
    with t2:
        st.markdown("### 👤 Öğrenci İşlemleri")
        islem = st.radio("İşlem:", ["➕ Yeni Ekle", "✏️ Güncelle", "🗑️ Sil"],
                         horizontal=True, label_visibility="collapsed")

        if islem == "➕ Yeni Ekle":
            with st.form("yeni_ogr", clear_on_submit=True):
                st.markdown("#### ➕ Yeni Öğrenci Bilgileri")
                c1, c2, c3 = st.columns(3)
                with c1:
                    yeni_no  = st.text_input("Okul No *")
                    yeni_ad  = st.text_input("Ad Soyad *")
                with c2:
                    yeni_sinif = st.text_input("Sınıf *", placeholder="6/A")
                    yeni_puan  = st.text_input("1. Dönem Puanı")
                with c3:
                    yeni_proje = st.text_input("Proje Konusu")
                    yeni_durum = st.selectbox("Durum", ["Zorunlu", "Gönüllü", "Proje Üst"])
                _, bb2, _ = st.columns([1, 1, 1])
                with bb2:
                    ekle_btn = st.form_submit_button("💾  Ekle", use_container_width=True)
                if ekle_btn:
                    if not all([yeni_no.strip(), yeni_ad.strip(), yeni_sinif.strip()]):
                        st.error("❌ Zorunlu alanları (*) doldurun.")
                    elif yeni_no.strip() in df['Okul No'].tolist():
                        st.error("❌ Bu numara zaten kayıtlı!")
                    else:
                        yeni_veri = {c: None for c in GEREKLI_SUTUNLAR}
                        yeni_veri.update({'Okul No': yeni_no.strip(), 'Öğrenci Adı Soyadı': yeni_ad.strip(),
                                          'Sınıf': yeni_sinif.strip(), '1. Dönem Puanı': yeni_puan,
                                          'Proje': yeni_proje, 'Durum': yeni_durum})
                        df.loc[len(df)] = yeni_veri
                        veriyi_kaydet(df)
                        st.success(f"✅ {yeni_ad} eklendi!")
                        st.rerun()

        elif islem == "✏️ Güncelle":
            if df.empty:
                st.warning("⚠️ Öğrenci yok.")
            else:
                ogr_listesi = df.apply(lambda r: f"{r['Sınıf']} — {r['Okul No']} — {r.get('Öğrenci Adı Soyadı','')}", axis=1).tolist()
                secim = st.selectbox("Öğrenci:", ["— Seçiniz —"] + ogr_listesi)
                if secim != "— Seçiniz —":
                    ono = secim.split(" — ")[1]
                    idx = df.index[df['Okul No'] == ono].tolist()[0]
                    with st.form("guncelle"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            gun_ad    = st.text_input("Ad Soyad", value=str(df.at[idx,'Öğrenci Adı Soyadı'] or ""))
                            gun_sinif = st.text_input("Sınıf",    value=str(df.at[idx,'Sınıf'] or ""))
                        with c2:
                            gun_puan  = st.text_input("1. Dönem", value=str(df.at[idx,'1. Dönem Puanı'] or ""))
                            gun_proje = st.text_input("Proje",    value=str(df.at[idx,'Proje'] or ""))
                        with c3:
                            ops = ["Zorunlu","Gönüllü","Proje Üst"]
                            di  = ops.index(df.at[idx,'Durum']) if df.at[idx,'Durum'] in ops else 0
                            gun_durum = st.selectbox("Durum", ops, index=di)
                        _, bb3, _ = st.columns([1,1,1])
                        with bb3:
                            gun_btn = st.form_submit_button("✏️  Güncelle", use_container_width=True)
                        if gun_btn:
                            df.at[idx,'Öğrenci Adı Soyadı'] = gun_ad.strip()
                            df.at[idx,'Sınıf']              = gun_sinif.strip()
                            df.at[idx,'1. Dönem Puanı']     = gun_puan
                            df.at[idx,'Proje']              = gun_proje
                            df.at[idx,'Durum']              = gun_durum
                            veriyi_kaydet(df)
                            st.success("✅ Güncellendi!"); st.rerun()

        else:  # Sil
            if df.empty:
                st.warning("⚠️ Öğrenci yok.")
            else:
                ogr_listesi_s = df.apply(lambda r: f"{r['Sınıf']} — {r['Okul No']} — {r.get('Öğrenci Adı Soyadı','')}", axis=1).tolist()
                secim_s = st.selectbox("Silinecek Öğrenci:", ["— Seçiniz —"] + ogr_listesi_s, key="sil_sec")
                if secim_s != "— Seçiniz —":
                    st.warning(f"⚠️ **{secim_s}** kaydını kalıcı silmek istediğinize emin misiniz?")
                    if st.button("🗑️  Evet, Kalıcı Sil", key="sil_btn"):
                        ono_s = secim_s.split(" — ")[1]
                        df_yeni = df[df['Okul No'] != ono_s].reset_index(drop=True)
                        veriyi_kaydet(df_yeni)
                        st.success("✅ Silindi."); st.rerun()

    # ─── SEKME 3: PUANLAMA VE AI ─────────────────────────────────
    with t3:
        st.markdown("### 🤖 Puanlama ve Yapay Zeka Değerlendirmesi")

        if df.empty:
            st.warning("⚠️ Önce sisteme öğrenci ekleyin.")
        else:
            ogr_listesi_p = df.apply(lambda r: f"{r['Sınıf']} — {r['Okul No']} — {r.get('Öğrenci Adı Soyadı','')}", axis=1).tolist()
            secim_p = st.selectbox("Değerlendirilecek Öğrenci:", ["— Seçiniz —"] + ogr_listesi_p, key="puan_sec")

            if secim_p != "— Seçiniz —":
                ono_p = secim_p.split(" — ")[1]
                idx   = df.index[df['Okul No'] == ono_p].tolist()[0]
                bilgi = df.iloc[idx]

                with st.expander("👁️ Güncel Karne Önizlemesi", expanded=False):
                    st.markdown(karne_html_olustur(bilgi), unsafe_allow_html=True)

                st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
                st.markdown("#### 🎯 Kriter Bazlı Puanlama")
                st.info("💡 Puanları girin, ardından **Yapay Zeka ile Doldur** butonuna tıklayın. Tüm açıklama kutuları otomatik dolacak.")

                # ── SESSION STATE BAŞLAT ──
                for k in KRITERLER:
                    pk = f"p_{idx}_{k['id']}"
                    ak = f"a_{idx}_{k['id']}"
                    if pk not in st.session_state:
                        db_p = df.at[idx, f"{k['baslik']} Puanı"]
                        st.session_state[pk] = int(pd.to_numeric(db_p, errors='coerce')) if pd.notna(db_p) else 0
                    if ak not in st.session_state:
                        db_a = df.at[idx, f"{k['baslik']} Açıklaması"]
                        st.session_state[ak] = str(db_a) if pd.notna(db_a) else ""

                gk = f"g_{idx}"
                if gk not in st.session_state:
                    db_g = df.at[idx, 'Genel Değerlendirme Yorumu']
                    st.session_state[gk] = str(db_g) if pd.notna(db_g) else ""

                # ── KRİTER KUTULARI ──
                toplam_anlik = 0
                for k in KRITERLER:
                    pk = f"p_{idx}_{k['id']}"
                    ak = f"a_{idx}_{k['id']}"
                    mevcut_p = st.session_state[pk]
                    oran_pct = int((mevcut_p / k['max']) * 100) if k['max'] > 0 else 0
                    r_bar    = puan_renk(mevcut_p, k['max'])

                    st.markdown(f"""
                    <div class="kriter-box">
                      <div class="kriter-baslik">{k['icon']} {k['baslik']}
                        <span style="color:rgba(255,255,255,0.3);font-weight:400;font-size:0.8rem;"> · Maks {k['max']} puan</span>
                      </div>
                      <div class="kriter-aciklama">{k['aciklama']}</div>
                    </div>""", unsafe_allow_html=True)

                    c_p, c_a = st.columns([1, 4])
                    with c_p:
                        st.number_input(f"Puan (0–{k['max']})", min_value=0, max_value=k['max'], key=pk)
                        st.markdown(f"""
                        <div class="puan-bar-wrapper">
                          <div class="puan-bar-fill" style="width:{oran_pct}%;background:{r_bar};"></div>
                        </div>
                        <div style="text-align:right;font-size:0.7rem;color:rgba(255,255,255,0.35);margin-top:2px;">{oran_pct}%</div>
                        """, unsafe_allow_html=True)
                    with c_a:
                        st.text_input("Açıklama (AI doldurur ya da siz yazın)", key=ak)

                    toplam_anlik += st.session_state[pk]

                # ── TOPLAM ──
                toplam_renk = puan_renk(toplam_anlik, 100)
                st.markdown(f"""
                <div style="display:flex;justify-content:center;margin:18px 0 10px;">
                  <div class="toplam-badge" style="background:linear-gradient(135deg,{toplam_renk}cc,{toplam_renk}88);border:1px solid {toplam_renk}55;">
                    {toplam_anlik} <span style="font-size:1rem;opacity:0.6;">/ 100</span>
                  </div>
                </div>""", unsafe_allow_html=True)

                st.text_area("📝 Genel Değerlendirme Yorumu (AI doldurur ya da siz yazın)", key=gk, height=105)

                st.markdown("---")
                st.markdown("#### 💬 Öğretmen Notu (Yapay Zekaya Ek Bilgi)")

                ham_metin = st.text_area(
                    "Ek not girin ya da boş bırakın",
                    placeholder=(
                        "Örn: 'Proje çok geç teslim edildi fakat içerik gerçekten kaliteliydi.'\n"
                        "Boş bırakırsanız AI sadece yukarıdaki puanlara ve öğrenci bilgilerine bakarak değerlendirme yapar."
                    ),
                    height=80, key=f"ham_{idx}", label_visibility="collapsed"
                )

                col_ai, col_save = st.columns(2)

                with col_ai:
                    st.markdown('<div class="ai-btn">', unsafe_allow_html=True)
                    ai_btn = st.button("✨  Yapay Zeka ile Tüm Açıklamaları Doldur",
                                       use_container_width=True, key="ai_btn")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_save:
                    st.markdown('<div class="kaydet-btn">', unsafe_allow_html=True)
                    save_btn = st.button("💾  Puanları ve Açıklamaları Kaydet",
                                         use_container_width=True, key="save_btn")
                    st.markdown('</div>', unsafe_allow_html=True)

                # ── AI ÇAĞRISI ──
                if ai_btn:
                    puanlar_dict = {k["id"]: st.session_state[f"p_{idx}_{k['id']}"] for k in KRITERLER}
                    with st.spinner("🤖 Gemini yapay zekası değerlendirme hazırlıyor..."):
                        try:
                            json_data = ai_degerlendirme_yap(bilgi.to_dict(), ham_metin, puanlar_dict)
                            for k in KRITERLER:
                                kid = k['id']
                                if kid in json_data:
                                    st.session_state[f"a_{idx}_{kid}"] = json_data[kid]
                            if "genel" in json_data:
                                st.session_state[gk] = json_data["genel"]
                            st.success("✅ Yapay zeka değerlendirmesi tamamlandı! Açıklamalar güncellendi.")
                            time.sleep(0.4); st.rerun()
                        except json.JSONDecodeError:
                            st.error("❌ AI geçersiz format döndürdü. Tekrar deneyin.")
                        except Exception as e:
                            st.error(f"❌ Hata oluştu: {e}")

                # ── KAYDET ──
                if save_btn:
                    for k in KRITERLER:
                        df.at[idx, f"{k['baslik']} Puanı"]      = st.session_state[f"p_{idx}_{k['id']}"]
                        df.at[idx, f"{k['baslik']} Açıklaması"] = st.session_state[f"a_{idx}_{k['id']}"]
                    df.at[idx, 'Genel Değerlendirme Yorumu'] = st.session_state[gk]
                    toplam_final = sum(st.session_state[f"p_{idx}_{k['id']}"] for k in KRITERLER)
                    df.at[idx, 'Toplam Puan'] = toplam_final
                    veriyi_kaydet(df)
                    st.success(f"✅ Kaydedildi! Toplam Puan: **{toplam_final}/100**")

    # ─── SEKME 4: RAPOR ──────────────────────────────────────────
    with t4:
        st.markdown("### 📊 Raporlama ve Karne Çıktıları")

        if df.empty:
            st.warning("⚠️ Raporlanacak veri yok.")
        else:
            mevcut_siniflar = sorted(df['Sınıf'].dropna().unique().tolist())
            fc, sc = st.columns([1, 2])
            with fc:
                filtre = st.radio("Görünüm:", ["🏫 Tüm Sınıflar", "📋 Tek Sınıf"], horizontal=False)
            with sc:
                if filtre == "📋 Tek Sınıf":
                    secili_sinif = st.selectbox("Sınıf:", mevcut_siniflar)
                    gosterilecek = df[df['Sınıf'] == secili_sinif]
                    dosya_adi = f"{secili_sinif.replace('/', '_')}_Rapor.xlsx"
                else:
                    gosterilecek   = df
                    secili_sinif   = None
                    dosya_adi = "Tum_Siniflar_Rapor.xlsx"

            goster_cols = (['Sınıf', 'Okul No', 'Öğrenci Adı Soyadı'] +
                           [f"{k['baslik']} Puanı" for k in KRITERLER] + ['Toplam Puan'])
            temiz = gosterilecek[[c for c in goster_cols if c in gosterilecek.columns]].copy()
            for k in KRITERLER:
                cn = f"{k['baslik']} Puanı"
                if cn in temiz.columns:
                    temiz[cn] = pd.to_numeric(temiz[cn], errors='coerce')
            if 'Toplam Puan' in temiz.columns:
                temiz['Toplam Puan'] = pd.to_numeric(temiz['Toplam Puan'], errors='coerce')
            st.dataframe(temiz, use_container_width=True, hide_index=True)

            st.markdown("#### 📥 İndirme Seçenekleri")
            dl1, dl2, dl3 = st.columns(3)

            with dl1:
                out1 = io.BytesIO()
                with pd.ExcelWriter(out1, engine='xlsxwriter') as w:
                    gosterilecek.to_excel(w, index=False, sheet_name='Rapor')
                st.download_button("📊  Excel İndir", data=out1.getvalue(),
                                   file_name=dosya_adi, use_container_width=True,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with dl2:
                out2 = io.BytesIO()
                with pd.ExcelWriter(out2, engine='xlsxwriter') as w:
                    for s in mevcut_siniflar:
                        df[df['Sınıf'] == s].to_excel(w, index=False, sheet_name=s.replace('/', '_'))
                st.download_button("📑  Tüm Sınıflar Excel", data=out2.getvalue(),
                                   file_name="Tum_Siniflar.xlsx", use_container_width=True,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with dl3:
                if filtre == "📋 Tek Sınıf":
                    html_k = toplu_karne_html_dosyasi_uret(gosterilecek)
                    st.download_button(
                        "🖨️  Karneleri İndir (HTML→PDF)",
                        data=html_k,
                        file_name=f"{secili_sinif.replace('/','_')}_Karneler.html",
                        mime="text/html", use_container_width=True,
                        help="Tarayıcıda aç → Ctrl+P → PDF olarak kaydet → WhatsApp'tan gönder."
                    )
                else:
                    st.info("💡 Karne çıktısı için 'Tek Sınıf' seçin.")

            if filtre == "🏫 Tüm Sınıflar":
                st.markdown("---")
                st.markdown("#### 📈 Sınıf Bazlı Puan Ortalamaları")
                ort_df = (df.groupby('Sınıf')['Toplam Puan']
                          .apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
                          .reset_index())
                ort_df.columns = ['Sınıf', 'Ortalama']
                ort_df = ort_df.dropna().sort_values('Sınıf')
                if not ort_df.empty:
                    st.bar_chart(ort_df.set_index('Sınıf'))


# ==========================================
# ANA FONKSİYON
# ==========================================
def main():
    st.markdown("""
    <div class="hero-header">
      <div class="hero-title">🏫 Gazi Ortaokulu</div>
      <div class="hero-subtitle">Matematik Proje Değerlendirme Sistemi &nbsp;·&nbsp; 2025-2026 Eğitim Öğretim Yılı</div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎓 Öğrenci Girişi", "👨‍🏫 Öğretmen Paneli"])
    df = veri_yukle()

    with tab1:
        ogrenci_paneli(df)
    with tab2:
        ogretmen_paneli(df)


if __name__ == "__main__":
    main()
