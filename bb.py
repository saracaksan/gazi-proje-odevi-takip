import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import json

# ==========================================
# 1. BÖLÜM: KURULUMLAR, VERİTABANI VE KARNE MOTORU
# ==========================================

st.set_page_config(page_title="Gazi Ortaokulu Proje Sistemi", page_icon="🎓", layout="wide")

API_KEY = "AIzaSyDR59-y8bOekDJBHjSN9vvFfjhWXQfPRUM"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

DATA_FILE = "veritabani.csv"

KRITERLER = [
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi ve konu hakimiyeti."},
    {"id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "aciklama": "Ödevin temiz, okunaklı ve düzenli bir şekilde hazırlanmış olması. Kağıt kullanımının özeni."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler veya açıklamalar eklenmesi."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi."},
    {"id": "k5", "baslik": "Zamanında Teslim", "max": 15, "aciklama": "Projenin belirtilen tarihte (26 Nisan 2026) teslim edilmesi."}
]

GEREKLI_SUTUNLAR = ['S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', '1. Dönem Puanı', 'Proje', 'Durum']
for k in KRITERLER:
    GEREKLI_SUTUNLAR.append(f"{k['baslik']} Puanı")
    GEREKLI_SUTUNLAR.append(f"{k['baslik']} Açıklaması")
GEREKLI_SUTUNLAR.extend(['Genel Değerlendirme Yorumu', 'Toplam Puan'])

# ── YENİ: Görseli güçlendiren CSS ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=Inter:wght@400;500;600&display=swap');

/* === GENEL === */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* === ARKAPLAN === */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f2044 100%) !important;
    min-height: 100vh;
}

/* === HERO BAŞLIK === */
.hero {
    background: linear-gradient(135deg, #1e40af, #2563eb, #3b82f6);
    border-radius: 20px; padding: 30px 40px; margin-bottom: 26px;
    text-align: center; box-shadow: 0 16px 48px rgba(37,99,235,0.45);
    position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; inset: -60%; width: 220%; height: 220%;
    background: radial-gradient(circle, rgba(255,255,255,0.07) 0%, transparent 65%);
    animation: spin 8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.hero h1 { font-family:'Nunito',sans-serif; font-size:2.2rem; font-weight:900;
    color:white; margin:0 0 5px; text-shadow:0 2px 8px rgba(0,0,0,0.25);
    position:relative; z-index:1; }
.hero p  { color:rgba(255,255,255,0.82); font-size:1rem; margin:0;
    position:relative; z-index:1; }

/* === SEKMELER === */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.05); border-radius:14px;
    padding:5px; border:1px solid rgba(255,255,255,0.1); gap:4px; margin-bottom:18px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius:10px; color:rgba(255,255,255,0.55) !important;
    font-weight:700; padding:9px 22px; border:none; transition:all 0.2s;
    background:transparent;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { background:rgba(255,255,255,0.08); color:white !important; }
[data-testid="stTabs"] [aria-selected="true"] {
    background:linear-gradient(135deg,#2563eb,#3b82f6) !important;
    color:white !important; box-shadow:0 4px 14px rgba(37,99,235,0.5);
}

/* === INPUT / TEXTAREA / SELECT === */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-radius: 10px !important; color: white !important;
    caret-color: white;
}
.stTextInput > div > div > input::placeholder,
.stTextArea  > div > div > textarea::placeholder { color:rgba(255,255,255,0.32) !important; }
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color:#3b82f6 !important; box-shadow:0 0 0 3px rgba(59,130,246,0.2) !important;
}

/* Selectbox: kutu + dropdown tamamen beyaz yazı */
[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-radius: 10px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] [data-baseweb="tag"],
[data-baseweb="select"] div { color: white !important; }
[data-baseweb="select"] svg { fill: white !important; }
[data-baseweb="popover"] {
    background: #1e293b !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
}
[data-baseweb="menu"] li { color: white !important; }
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] { background: rgba(59,130,246,0.25) !important; }

/* Etiketler */
label,
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stRadio label,
[data-testid="stWidgetLabel"] p {
    color: rgba(255,255,255,0.78) !important;
    font-weight: 600 !important; font-size: 0.84rem !important;
}

/* === BUTONLAR === */
.stButton > button {
    background: linear-gradient(135deg,#2563eb,#3b82f6) !important;
    color: white !important; border: none !important; border-radius: 11px !important;
    padding: 11px 22px !important; font-weight: 700 !important;
    font-family: 'Nunito',sans-serif !important; transition: all 0.22s !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.38) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 22px rgba(37,99,235,0.58) !important; }
.stButton > button:active { transform: translateY(0) !important; }

.stDownloadButton > button {
    background: linear-gradient(135deg,#059669,#10b981) !important;
    color: white !important; border: none !important; border-radius: 11px !important;
    font-weight: 700 !important; box-shadow: 0 4px 14px rgba(5,150,105,0.38) !important;
    transition: all 0.22s !important;
}
.stDownloadButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 22px rgba(5,150,105,0.55) !important; }

/* Özel buton renkleri */
div[data-testid="stButton-ai"] button   { background:linear-gradient(135deg,#7c3aed,#a855f7) !important; box-shadow:0 4px 18px rgba(124,58,237,0.45) !important; }
div[data-testid="stButton-save"] button { background:linear-gradient(135deg,#059669,#10b981) !important; box-shadow:0 4px 18px rgba(5,150,105,0.45) !important; }

/* === MESAJ KUTULARI === */
[data-testid="stSuccess"] { background:rgba(16,185,129,0.13) !important; border:1px solid rgba(16,185,129,0.3) !important; border-radius:11px !important; }
[data-testid="stError"]   { background:rgba(239,68,68,0.13)  !important; border:1px solid rgba(239,68,68,0.3)  !important; border-radius:11px !important; }
[data-testid="stWarning"] { background:rgba(245,158,11,0.13) !important; border:1px solid rgba(245,158,11,0.3) !important; border-radius:11px !important; }
[data-testid="stInfo"]    { background:rgba(59,130,246,0.13) !important; border:1px solid rgba(59,130,246,0.3)  !important; border-radius:11px !important; }

/* === TABLO === */
[data-testid="stDataFrame"] { border-radius:13px; overflow:hidden; }

/* === EXPANDER === */
[data-testid="stExpander"] {
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:13px !important;
}

/* === FORM === */
[data-testid="stForm"] {
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);
    border-radius:14px; padding:18px;
}

/* === RADIO === */
.stRadio > div { gap:10px; }
[data-testid="stRadio"] label {
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    border-radius:9px !important; padding:7px 15px !important;
    transition:all 0.2s !important;
}
[data-testid="stRadio"] label:hover { background:rgba(59,130,246,0.15) !important; }

/* === METİN RENKLERİ === */
p, span, div, li { color: rgba(255,255,255,0.85); }
h1,h2,h3,h4 { color: white !important; font-family:'Nunito',sans-serif !important; font-weight:800 !important; }
strong { color: white !important; }

/* === SCROLLBAR === */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:rgba(255,255,255,0.04); }
::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.18); border-radius:3px; }

/* === YENİ: KRITER KUTUSU === */
.kriter-kutu {
    background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.09);
    border-radius:13px; padding:14px 18px; margin-bottom:12px; transition:border-color 0.2s;
}
.kriter-kutu:hover { border-color:rgba(59,130,246,0.38); }

/* === YENİ: METRİK KARTI === */
.mk {
    background:linear-gradient(135deg,rgba(37,99,235,0.28),rgba(59,130,246,0.12));
    border:1px solid rgba(96,165,250,0.28); border-radius:15px;
    padding:18px; text-align:center;
}
.mk-val { font-family:'Nunito',sans-serif; font-size:2rem; font-weight:900; color:#60a5fa; line-height:1; }
.mk-lbl { font-size:0.73rem; color:rgba(255,255,255,0.48); margin-top:5px; font-weight:600;
           text-transform:uppercase; letter-spacing:0.4px; }

/* === YENİ: PUAN PROGRESS BAR === */
.pb-wrap { width:100%; height:6px; background:rgba(255,255,255,0.1); border-radius:6px; overflow:hidden; margin-top:4px; }
.pb-fill  { height:100%; border-radius:6px; transition:width 0.5s; }

/* === YENİ: TOPLAM PUAN BADGE === */
.toplam-badge {
    background:linear-gradient(135deg,#1e40af,#2563eb);
    border:1px solid rgba(96,165,250,0.3); color:white;
    font-family:'Nunito',sans-serif; font-size:1.7rem; font-weight:900;
    border-radius:14px; padding:14px 36px; text-align:center;
    box-shadow:0 6px 20px rgba(37,99,235,0.4); display:inline-block;
}
.divider { height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.14),transparent); margin:18px 0; }
</style>
""", unsafe_allow_html=True)

# ── HERO BAŞLIK ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🏫 Gazi Ortaokulu</h1>
  <p>Matematik Proje Değerlendirme Sistemi &nbsp;·&nbsp; 2025-2026 Eğitim Öğretim Yılı</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# VERİ FONKSİYONLARI
# ==========================================

@st.cache_data(ttl=0)
def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype={"Okul No": str})
            df.dropna(subset=['Okul No'], inplace=True)
            df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
            for sutun in GEREKLI_SUTUNLAR:
                if sutun not in df.columns:
                    df[sutun] = None
            return df
        except:
            return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
    return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

def veriyi_kaydet(df):
    df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()   # ← YENİ: kaydedince cache temizlenir

def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', '1. Dönem Puanı', 'Proje', 'Durum'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Sablonu')
        ws = writer.sheets['Ogrenci_Sablonu']
        for col_num in range(len(sablon_df.columns)):
            ws.set_column(col_num, col_num, 22)
    return output.getvalue()

# ── YENİ: puan rengini döndüren yardımcı fonksiyon ──
def puan_renk(puan, maks):
    oran = puan / maks if maks > 0 else 0
    if oran >= 0.85: return "#10b981"
    elif oran >= 0.60: return "#f59e0b"
    return "#ef4444"

# ==========================================
# KARNE HTML MOTORU  (orijinal + görsel iyileştirme)
# ==========================================

def karne_html_olustur(bilgi):
    toplam_puan = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
    toplam_puan = 0 if pd.isna(toplam_puan) else int(toplam_puan)
    tp_renk = puan_renk(toplam_puan, 100)

    # ── Kriter satırları ──
    tablo_html = """
    <div style="overflow-x:auto;">
    <table style="width:100%;border:1px solid #ddd;border-collapse:collapse;font-family:Arial,sans-serif;">
      <tr style="background-color:#1E3A8A;color:white;">
        <th style="padding:12px;border:1px solid #ddd;width:30%;">Değerlendirme Kriterleri</th>
        <th style="padding:12px;border:1px solid #ddd;text-align:center;width:10%;">Puan Değeri</th>
        <th style="padding:12px;border:1px solid #ddd;text-align:center;width:10%;">Alınan Puan</th>
        <th style="padding:12px;border:1px solid #ddd;width:50%;">Öğretmen / Yapay Zeka Açıklaması</th>
      </tr>
    """
    for k in KRITERLER:
        puan = pd.to_numeric(bilgi.get(f"{k['baslik']} Puanı", 0), errors='coerce')
        puan = 0 if pd.isna(puan) else int(puan)
        aciklama = bilgi.get(f"{k['baslik']} Açıklaması", "")
        aciklama = "Değerlendirme girilmedi." if pd.isna(aciklama) or str(aciklama).strip() == "" else str(aciklama)
        renk = puan_renk(puan, k['max'])
        oran = int((puan / k['max']) * 100) if k['max'] > 0 else 0
        tablo_html += f"""
      <tr>
        <td style="padding:10px;border:1px solid #ddd;">
          <b>{k['baslik']}</b><br>
          <span style="font-size:12px;color:#555;">{k['aciklama']}</span>
        </td>
        <td style="padding:10px;border:1px solid #ddd;text-align:center;font-size:16px;">{k['max']}</td>
        <td style="padding:10px;border:1px solid #ddd;text-align:center;">
          <span style="font-size:18px;font-weight:bold;color:{renk};">{puan}</span><br>
          <div style="width:100%;height:4px;background:#e5e7eb;border-radius:4px;margin-top:4px;overflow:hidden;">
            <div style="width:{oran}%;height:100%;background:{renk};border-radius:4px;"></div>
          </div>
        </td>
        <td style="padding:10px;border:1px solid #ddd;color:#2E7D32;font-style:italic;">{aciklama}</td>
      </tr>
        """
    genel_yorum = bilgi.get('Genel Değerlendirme Yorumu', '')
    genel_yorum = "Henüz genel değerlendirme yapılmadı." if pd.isna(genel_yorum) or str(genel_yorum).strip() == "" else str(genel_yorum)

    tablo_html += f"""
      <tr style="background-color:#f2f2f2;">
        <td style="padding:12px;border:1px solid #ddd;text-align:right;font-size:18px;" colspan="2"><b>TOPLAM PUAN:</b></td>
        <td style="padding:12px;border:1px solid #ddd;text-align:center;color:{tp_renk};font-size:22px;font-weight:bold;">{toplam_puan}</td>
        <td style="padding:12px;border:1px solid #ddd;font-size:14px;"><b>Genel Değerlendirme:</b><br>{genel_yorum}</td>
      </tr>
    </table>
    </div>
    """
    return tablo_html


def toplu_karne_html_dosyasi_uret(df_sinif):
    html_icerik = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>Toplu Proje Karneleri</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f9f9f9; }
            .karne-sayfasi {
                background-color: white; width: 210mm; min-height: 297mm;
                margin: 0 auto; padding: 20mm; box-sizing: border-box;
                page-break-after: always; box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .baslik { text-align: center; color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; margin-bottom: 20px;}
            @media print {
                body { background-color: white; }
                .karne-sayfasi { box-shadow: none; margin: 0; padding: 10mm; width: auto; min-height: auto;}
            }
        </style>
    </head>
    <body>
    """
    for i in range(len(df_sinif)):
        bilgi = df_sinif.iloc[i]
        html_icerik += f"""
        <div class="karne-sayfasi">
            <div class="baslik">
                <h2>GAZİ ORTAOKULU</h2>
                <h3>Matematik Proje Değerlendirme Karnesi</h3>
            </div>
            <p><strong>👤 Öğrenci:</strong> {bilgi.get('Öğrenci Adı Soyadı','')} &nbsp;|&nbsp; <strong>Sınıf:</strong> {bilgi.get('Sınıf','')} &nbsp;|&nbsp; <strong>Okul No:</strong> {bilgi.get('Okul No','')}</p>
            <p><strong>Proje Konusu:</strong> {bilgi.get('Proje','-')} &nbsp;|&nbsp; <strong>1. Dönem Puanı:</strong> {bilgi.get('1. Dönem Puanı','-')}</p>
        """
        html_icerik += karne_html_olustur(bilgi)
        html_icerik += """
            <div style="margin-top: 50px; text-align: right;">
                <strong>Ders Öğretmeni</strong><br>
                Sıraç AKSAN
            </div>
        </div>
        """
    html_icerik += "</body></html>"
    return html_icerik


# ==========================================
# ÖĞRENCİ PANELİ  (orijinal + görsel iyileştirme)
# ==========================================

def ogrenci_paneli(df):
    st.markdown("### 🔍 Öğrenci Sonuç Sorgulama Ekranı")
    if df.empty or len(df.columns) < 10:
        st.warning("Sisteme henüz veri yüklenmemiştir.")
        return

    col1, col2 = st.columns(2)
    with col1:
        siniflar = ["Seçiniz"] + sorted(list(df['Sınıf'].dropna().unique()))
        sinif = st.selectbox("Sınıfınız:", siniflar, key="ogr_sinif")
    with col2:
        okul_no = st.text_input("Okul Numaranız:", key="ogr_no")

    if st.button("📄 Sonucumu Göster", use_container_width=True):
        if sinif == "Seçiniz" or not okul_no:
            st.error("Lütfen sınıfınızı ve numaranızı eksiksiz girin!")
        else:
            ogrenci = df[(df['Sınıf'] == sinif) & (df['Okul No'] == str(okul_no).strip())]
            if ogrenci.empty:
                st.error("Sistemde bu bilgilere ait kayıt bulunamadı.")
            else:
                st.success("Sonuçlarınız başarıyla yüklendi!")
                bilgi = ogrenci.iloc[0]
                toplam = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
                toplam = 0 if pd.isna(toplam) else int(toplam)

                # YENİ: özet metrik kartları
                st.markdown(f"### 👤 {bilgi.get('Öğrenci Adı Soyadı','Bilinmiyor')} — {bilgi.get('Sınıf','')}")
                st.markdown(f"**Proje Konusu:** {bilgi.get('Proje','-')} &nbsp;|&nbsp; **Durum:** {bilgi.get('Durum','-')} &nbsp;|&nbsp; **1. Dönem Puanı:** {bilgi.get('1. Dönem Puanı','-')}")

                m1, m2, m3 = st.columns(3)
                with m1:
                    r = puan_renk(toplam, 100)
                    st.markdown(f'<div class="mk"><div class="mk-val" style="color:{r};">{toplam}</div><div class="mk-lbl">Toplam Puan / 100</div></div>', unsafe_allow_html=True)
                with m2:
                    basari = "Mükemmel 🏆" if toplam >= 90 else ("Çok İyi ⭐" if toplam >= 75 else ("İyi 👍" if toplam >= 60 else "Geliştirilmeli 📈"))
                    st.markdown(f'<div class="mk"><div class="mk-val" style="font-size:1.1rem;">{basari}</div><div class="mk-lbl">Başarı Durumu</div></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="mk"><div class="mk-val" style="font-size:1.1rem;">{bilgi.get("Durum","-")}</div><div class="mk-lbl">Proje Durumu</div></div>', unsafe_allow_html=True)

                st.markdown("---")
                st.markdown(karne_html_olustur(bilgi), unsafe_allow_html=True)


# ==========================================
# 2. BÖLÜM: ÖĞRETMEN PANELİ VE AI OTOMASYONU
# ==========================================

def ogretmen_paneli(df):
    # YENİ: oturum kalıcılığı
    if "ogretmen_giris" not in st.session_state:
        st.session_state["ogretmen_giris"] = False

    if not st.session_state["ogretmen_giris"]:
        sifre = st.text_input("Yönetici Şifresi:", type="password", key="admin_pass")
        if st.button("Giriş Yap"):
            if sifre == "Sarac.47":
                st.session_state["ogretmen_giris"] = True
                st.rerun()
            elif sifre:
                st.error("Hatalı şifre!")
        return

    # ── Giriş başarılı ──
    col_hosgeldin, col_cikis = st.columns([5, 1])
    with col_hosgeldin:
        st.success("Yönetici Girişi Başarılı! Hoş Geldiniz Sıraç Hocam.")
    with col_cikis:
        if st.button("🚪 Çıkış Yap"):
            st.session_state["ogretmen_giris"] = False
            st.rerun()

    otab1, otab2, otab3, otab4 = st.tabs([
        "📂 1. Toplu Veri Yükleme",
        "👤 2. Öğrenci İşlemleri",
        "🎙️ 3. Puanlama & Yapay Zeka",
        "📊 4. Rapor & Toplu PDF (WhatsApp)"
    ])

    # ─────────────────────────────────────────────────────────────
    # SEKME 1: Toplu Veri Yükleme  (orijinal + YENİ istatistik)
    # ─────────────────────────────────────────────────────────────
    with otab1:
        st.markdown("### 📥 Şablon İndirme ve Veri Yükleme")
        st.download_button(
            label="⬇️ Boş Excel Şablonunu İndir",
            data=bos_sablon_olustur(),
            file_name="Ogrenci_Veri_Sablonu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("#### 📤 Doldurduğunuz Şablonu Sisteme Yükleyin")
        yuklenen_dosya = st.file_uploader(
            "Dosyanızı buraya sürükleyin (Sadece yeni öğrenciler eklenir)",
            type=['xlsx', 'csv']
        )
        if yuklenen_dosya:
            if st.button("Verileri Sisteme Kaydet", use_container_width=True):
                try:
                    if yuklenen_dosya.name.endswith('.csv'):
                        yeni_df = pd.read_csv(yuklenen_dosya, dtype={"Okul No": str})
                    else:
                        yeni_df = pd.read_excel(yuklenen_dosya, dtype={"Okul No": str})
                    yeni_df['Okul No'] = yeni_df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
                    yeni_df.dropna(subset=['Okul No'], inplace=True)
                    mevcut_nolar = df['Okul No'].tolist()
                    eklenecek_df = yeni_df[~yeni_df['Okul No'].isin(mevcut_nolar)]
                    if eklenecek_df.empty:
                        st.warning("Tüm öğrenciler zaten kayıtlı! (Çift kayıt engellendi)")
                    else:
                        eklenecek_df = eklenecek_df.copy()
                        for sutun in GEREKLI_SUTUNLAR:
                            if sutun not in eklenecek_df.columns:
                                eklenecek_df[sutun] = None
                        df = pd.concat([df, eklenecek_df], ignore_index=True)
                        veriyi_kaydet(df)
                        st.success(f"Tebrikler! {len(eklenecek_df)} yeni öğrenci eklendi.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")

        # YENİ: genel istatistik özeti
        if not df.empty:
            st.markdown("---")
            st.markdown("#### 📈 Sistem İstatistikleri")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown(f'<div class="mk"><div class="mk-val">{len(df)}</div><div class="mk-lbl">Toplam Öğrenci</div></div>', unsafe_allow_html=True)
            with s2:
                deg = int(df['Toplam Puan'].notna().sum())
                st.markdown(f'<div class="mk"><div class="mk-val">{deg}</div><div class="mk-lbl">Değerlendirilen</div></div>', unsafe_allow_html=True)
            with s3:
                st.markdown(f'<div class="mk"><div class="mk-val">{df["Sınıf"].nunique()}</div><div class="mk-lbl">Sınıf Sayısı</div></div>', unsafe_allow_html=True)
            with s4:
                ort = pd.to_numeric(df['Toplam Puan'], errors='coerce').mean()
                ort_str = f"{ort:.1f}" if not pd.isna(ort) else "—"
                st.markdown(f'<div class="mk"><div class="mk-val">{ort_str}</div><div class="mk-lbl">Genel Ortalama</div></div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # SEKME 2: Manuel Öğrenci İşlemleri  (orijinal + YENİ: silme)
    # ─────────────────────────────────────────────────────────────
    with otab2:
        st.markdown("### 👤 Manuel Öğrenci İşlemleri")
        islem_tipi = st.radio(
            "İşlemi Seçin:",
            ("Yeni Öğrenci Ekle", "Mevcut Öğrenciyi Güncelle", "Öğrenci Sil"),   # YENİ: silme seçeneği
            horizontal=True
        )

        # ── Yeni öğrenci ekle (orijinal) ──────────────────────────
        if islem_tipi == "Yeni Öğrenci Ekle":
            with st.form("yeni_ogrenci_formu"):
                col1, col2 = st.columns(2)
                with col1:
                    yeni_no    = st.text_input("Okul Numarası *")
                    yeni_ad    = st.text_input("Öğrenci Adı Soyadı *")
                    yeni_sinif = st.text_input("Sınıfı (Örn: 6/A) *")
                with col2:
                    yeni_puan  = st.text_input("1. Dönem Puanı")
                    yeni_proje = st.text_input("Proje Konusu")
                    yeni_durum = st.selectbox("Durum", ["Zorunlu", "Gönüllü", "Proje Üst"])
                if st.form_submit_button("Yeni Öğrenciyi Kaydet"):
                    if not yeni_no or not yeni_ad or not yeni_sinif:
                        st.error("Lütfen yıldızlı (*) alanları doldurun.")
                    elif yeni_no.strip() in df['Okul No'].tolist():
                        st.error("HATA: Öğrenci sistemde zaten kayıtlı!")
                    else:
                        yeni_veri = {col: None for col in GEREKLI_SUTUNLAR}
                        yeni_veri['Okul No'] = yeni_no.strip()
                        yeni_veri['Öğrenci Adı Soyadı'] = yeni_ad.strip()
                        yeni_veri['Sınıf'] = yeni_sinif.strip()
                        yeni_veri['1. Dönem Puanı'] = yeni_puan
                        yeni_veri['Proje'] = yeni_proje
                        yeni_veri['Durum'] = yeni_durum
                        df.loc[len(df)] = yeni_veri
                        veriyi_kaydet(df)
                        st.success("Öğrenci eklendi!")
                        st.rerun()

        # ── Güncelle (orijinal) ───────────────────────────────────
        elif islem_tipi == "Mevcut Öğrenciyi Güncelle":
            if df.empty:
                st.warning("Güncellenecek öğrenci yok.")
            else:
                ogrenci_listesi = df.apply(
                    lambda row: f"{row['Sınıf']} - {row['Okul No']} - {row.get('Öğrenci Adı Soyadı', '')}",
                    axis=1
                ).tolist()
                secilen_ogrenci = st.selectbox("Öğrenciyi Seçin:", ["Seçiniz"] + ogrenci_listesi)
                if secilen_ogrenci != "Seçiniz":
                    secilen_okul_no = secilen_ogrenci.split(" - ")[1]
                    idx = df.index[df['Okul No'] == secilen_okul_no].tolist()[0]
                    with st.form("guncelle_formu"):
                        c1, c2 = st.columns(2)
                        with c1:
                            gun_no    = st.text_input("Okul Numarası", value=df.at[idx, 'Okul No'], disabled=True)
                            gun_ad    = st.text_input("Öğrenci Adı",   value=df.at[idx, 'Öğrenci Adı Soyadı'])
                            gun_sinif = st.text_input("Sınıfı",        value=df.at[idx, 'Sınıf'])
                        with c2:
                            gun_puan  = st.text_input("1. Dönem Puanı", value=str(df.at[idx, '1. Dönem Puanı']) if not pd.isna(df.at[idx, '1. Dönem Puanı']) else "")
                            gun_proje = st.text_input("Proje Konusu",   value=str(df.at[idx, 'Proje']) if not pd.isna(df.at[idx, 'Proje']) else "")
                            d_index   = ["Zorunlu", "Gönüllü", "Proje Üst"].index(df.at[idx, 'Durum']) if df.at[idx, 'Durum'] in ["Zorunlu", "Gönüllü", "Proje Üst"] else 0
                            gun_durum = st.selectbox("Durum", ["Zorunlu", "Gönüllü", "Proje Üst"], index=d_index)
                        if st.form_submit_button("Bilgileri Güncelle"):
                            df.at[idx, 'Öğrenci Adı Soyadı'] = gun_ad.strip()
                            df.at[idx, 'Sınıf']              = gun_sinif.strip()
                            df.at[idx, '1. Dönem Puanı']     = gun_puan
                            df.at[idx, 'Proje']              = gun_proje
                            df.at[idx, 'Durum']              = gun_durum
                            veriyi_kaydet(df)
                            st.success("Öğrenci güncellendi!")
                            st.rerun()

        # ── YENİ: Öğrenci Sil ─────────────────────────────────────
        elif islem_tipi == "Öğrenci Sil":
            if df.empty:
                st.warning("Silinecek öğrenci yok.")
            else:
                ogrenci_listesi_s = df.apply(
                    lambda row: f"{row['Sınıf']} - {row['Okul No']} - {row.get('Öğrenci Adı Soyadı', '')}",
                    axis=1
                ).tolist()
                secilen_sil = st.selectbox("Silinecek Öğrenci:", ["Seçiniz"] + ogrenci_listesi_s, key="sil_sec")
                if secilen_sil != "Seçiniz":
                    st.warning(f"⚠️ **{secilen_sil}** kaydı kalıcı olarak silinecek. Emin misiniz?")
                    col_evet, col_hayir = st.columns([1, 3])
                    with col_evet:
                        if st.button("🗑️ Evet, Sil", key="sil_btn"):
                            sil_no = secilen_sil.split(" - ")[1]
                            df = df[df['Okul No'] != sil_no].reset_index(drop=True)
                            veriyi_kaydet(df)
                            st.success("Öğrenci silindi.")
                            st.rerun()

    # ─────────────────────────────────────────────────────────────
    # SEKME 3: Puanlama & Yapay Zeka  (orijinal mantık korundu,
    #          session state key hatası düzeltildi, AI prompt zenginleştirildi)
    # ─────────────────────────────────────────────────────────────
    with otab3:
        st.markdown("### ✍️ Öğrenci Puanlama ve Değerlendirme")
        if df.empty or len(df.columns) < 10:
            st.warning("Lütfen önce sisteme öğrenci ekleyin.")
        else:
            ogrenci_listesi = df.apply(
                lambda row: f"{row['Sınıf']} - {row['Okul No']} - {row.get('Öğrenci Adı Soyadı', '')}",
                axis=1
            ).tolist()
            secilen_ogrenci = st.selectbox("Puanlanacak Öğrenciyi Seçin:", ["Seçiniz"] + ogrenci_listesi)

            if secilen_ogrenci != "Seçiniz":
                secilen_okul_no = secilen_ogrenci.split(" - ")[1]
                idx = df.index[df['Okul No'] == secilen_okul_no].tolist()[0]
                bilgi = df.iloc[idx]

                with st.expander("👁️ Tıkla: Öğrencinin Karnesi Şu An Nasıl Görünüyor?", expanded=False):
                    st.markdown(karne_html_olustur(bilgi), unsafe_allow_html=True)

                st.markdown("#### 🎯 Kriter Bazlı Puanlama")
                st.info("Puanları girin. En alttaki YAPAY ZEKA butonuna bastığınızda bu kutuların hepsi otomatik olarak dolacaktır.")

                # ── Session state başlat (key'ler artık tek tırnak içermez) ──
                toplam_anlik = 0
                for k in KRITERLER:
                    kid = k['id']
                    puan_key    = f"puan_{idx}_{kid}"
                    aciklama_key = f"aciklama_{idx}_{kid}"

                    if puan_key not in st.session_state:
                        db_puan = df.at[idx, f"{k['baslik']} Puanı"]
                        st.session_state[puan_key] = int(pd.to_numeric(db_puan, errors='coerce')) if pd.notna(db_puan) else 0

                    if aciklama_key not in st.session_state:
                        db_aciklama = df.at[idx, f"{k['baslik']} Açıklaması"]
                        st.session_state[aciklama_key] = str(db_aciklama) if pd.notna(db_aciklama) else ""

                # ── Kriter kutuları ──
                for k in KRITERLER:
                    kid = k['id']
                    puan_key     = f"puan_{idx}_{kid}"
                    aciklama_key = f"aciklama_{idx}_{kid}"
                    mevcut_p = st.session_state[puan_key]
                    oran_pct = int((mevcut_p / k['max']) * 100) if k['max'] > 0 else 0
                    r_bar    = puan_renk(mevcut_p, k['max'])

                    # YENİ: görsel kriter kutusu
                    st.markdown(f"""
                    <div class="kriter-kutu">
                      <b style="color:#93c5fd;">{k['baslik']}</b>
                      <span style="color:rgba(255,255,255,0.38);font-size:0.8rem;"> · Maks {k['max']} puan</span><br>
                      <span style="color:rgba(255,255,255,0.42);font-size:0.76rem;font-style:italic;">{k['aciklama']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.number_input(f"Puan (Max: {k['max']})", min_value=0, max_value=k['max'], key=puan_key)
                        # YENİ: progress bar
                        st.markdown(f"""
                        <div class="pb-wrap"><div class="pb-fill" style="width:{oran_pct}%;background:{r_bar};"></div></div>
                        <div style="text-align:right;font-size:0.68rem;color:rgba(255,255,255,0.35);margin-top:2px;">{oran_pct}%</div>
                        """, unsafe_allow_html=True)
                    with c2:
                        st.text_input("Açıklama (AI doldurur veya siz yazın):", key=aciklama_key)

                    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                    toplam_anlik += st.session_state[puan_key]

                # YENİ: dinamik renkli toplam badge
                tb_renk = puan_renk(toplam_anlik, 100)
                st.markdown(f"""
                <div style="display:flex;justify-content:center;margin:16px 0;">
                  <div class="toplam-badge" style="background:linear-gradient(135deg,{tb_renk}cc,{tb_renk}88);border:1px solid {tb_renk}55;">
                    {toplam_anlik} <span style="font-size:0.9rem;opacity:0.65;">/ 100 Puan</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                genel_key = f"genel_{idx}"
                if genel_key not in st.session_state:
                    db_genel = df.at[idx, 'Genel Değerlendirme Yorumu']
                    st.session_state[genel_key] = str(db_genel) if pd.notna(db_genel) else ""

                st.text_area("👩‍🏫 Karne Altı Genel Yorum (AI doldurur veya siz yazın):", key=genel_key, height=100)

                st.markdown("---")
                st.markdown("#### 🤖 Yapay Zeka Asistanı (Motivasyon Uzmanı)")
                ham_metin = st.text_area(
                    "💡 İsteğe bağlı öğretmen notu (Boş bırakırsanız AI sadece puanlara ve öğrenci bilgilerine bakarak yorum yazar):",
                    height=80,
                    placeholder="Örn: 'Ödev çok geç teslim edildi ama içerik gerçekten iyiydi.'"
                )

                col_ai, col_save = st.columns(2)

                with col_ai:
                    if st.button("✨ Yapay Zeka İle Tüm Açıklamaları Doldur", use_container_width=True):
                        with st.spinner("Yapay Zeka değerlendirme hazırlıyor..."):
                            try:
                                # YENİ: puan özetini değişken üzerinden oluştur (iç içe f-string hatası giderildi)
                                puan_parcalari = []
                                for k in KRITERLER:
                                    kid = k['id']
                                    p = st.session_state[f"puan_{idx}_{kid}"]
                                    puan_parcalari.append(f"{k['baslik']}: {p}/{k['max']}")
                                puan_ozeti = ", ".join(puan_parcalari)

                                # YENİ: öğrenci bilgilerini de prompt'a ekle
                                ogrenci_adi   = bilgi.get('Öğrenci Adı Soyadı', 'Öğrenci')
                                sinif_bilgisi = bilgi.get('Sınıf', '')
                                proje_konusu  = bilgi.get('Proje', '')
                                d1_puan       = bilgi.get('1. Dönem Puanı', '')
                                durum_bilgisi = bilgi.get('Durum', '')

                                not_kismi = ham_metin.strip() if ham_metin.strip() else \
                                    "Öğretmen ek notu yok; sadece puanlara ve öğrenci bilgilerine göre değerlendir."

                                prompt = f"""
Sen Gazi Ortaokulu'nda görev yapan deneyimli, anlayışlı ve motive edici bir ortaokul matematik öğretmenisin.

ÖĞRENCİ BİLGİLERİ:
- Ad Soyad     : {ogrenci_adi}
- Sınıf        : {sinif_bilgisi}
- Proje Konusu : {proje_konusu}
- 1. Dönem Notu: {d1_puan}
- Durum        : {durum_bilgisi}

PROJE PUANLARI:
{puan_ozeti}

ÖĞRETMEN NOTU:
{not_kismi}

GÖREVLER:
1) Her kriter için öğrenciye doğrudan "sen" diliyle hitap eden, 1-2 cümlelik ÖZGÜN ve YAPICI açıklama yaz.
   - Yüksek puan (≥%85): Samimi tebrik + bu başarının nedeni.
   - Orta puan (%60-84): Güçlü yön öne çık + nazik gelişim önerisi.
   - Düşük puan (<%60): Asla cesaretini kırma; eksikliği şefkatle ifade et.
   - Öğretmen notu varsa mutlaka dikkate al.
2) "genel" yorumda: Önce matematiğin günlük hayattaki önemine değin. Ardından {ogrenci_adi} adını kullanarak projenin genel bir değerlendirmesini yap. Motive edici bir kapanış cümlesi ekle.

SADECE AŞAĞIDAKİ JSON FORMATINDA ÇIKTI VER (başka hiçbir şey ekleme):
{{
    "k1": "İçerik ve Bilgi Doğruluğu açıklaması",
    "k2": "Düzen ve Tertip açıklaması",
    "k3": "Araştırma ve Zenginleştirme açıklaması",
    "k4": "Yaratıcılık ve Sunum açıklaması",
    "k5": "Zamanında Teslim açıklaması",
    "genel": "Genel motivasyon yorumu"
}}
"""
                                response = model.generate_content(
                                    prompt,
                                    generation_config={"response_mime_type": "application/json"}
                                )

                                raw_text  = response.text.replace('```json', '').replace('```', '').strip()
                                json_data = json.loads(raw_text)

                                # Session state'e yaz (orijinal mantık)
                                for k in KRITERLER:
                                    kid = k['id']
                                    if kid in json_data:
                                        st.session_state[f"aciklama_{idx}_{kid}"] = json_data[kid]
                                if "genel" in json_data:
                                    st.session_state[genel_key] = json_data["genel"]

                                st.rerun()
                            except Exception as e:
                                st.error(f"Hata oluştu. İnternet bağlantınızı kontrol edin. Detay: {e}")

                with col_save:
                    if st.button("💾 Tüm Puanları ve Açıklamaları Kaydet", use_container_width=True):
                        for k in KRITERLER:
                            kid = k['id']
                            df.at[idx, f"{k['baslik']} Puanı"]      = st.session_state[f"puan_{idx}_{kid}"]
                            df.at[idx, f"{k['baslik']} Açıklaması"] = st.session_state[f"aciklama_{idx}_{kid}"]

                        df.at[idx, 'Genel Değerlendirme Yorumu'] = st.session_state[genel_key]
                        toplam = sum(st.session_state[f"puan_{idx}_{k['id']}"] for k in KRITERLER)
                        df.at[idx, 'Toplam Puan'] = toplam

                        veriyi_kaydet(df)
                        st.success(f"{secilen_ogrenci} başarıyla kaydedildi! Toplam Puan: {toplam}/100")

    # ─────────────────────────────────────────────────────────────
    # SEKME 4: Rapor & Toplu PDF  (orijinal + YENİ: sınıf grafiği)
    # ─────────────────────────────────────────────────────────────
    with otab4:
        st.markdown("### 📊 Sınıf Karneleri ve Raporlama")
        if df.empty:
            st.warning("Şu an sistemde raporlanacak veri bulunmuyor.")
        else:
            mevcut_siniflar = sorted(df['Sınıf'].dropna().unique().tolist())
            filtre_tipi = st.radio(
                "Rapor Görünümü:",
                ["Tüm Sınıflar (Toplu)", "Sınıf Bazlı (Tek Sınıf)"],
                horizontal=True
            )

            if filtre_tipi == "Sınıf Bazlı (Tek Sınıf)":
                secili_sinif    = st.selectbox("Listelenecek Sınıfı Seçin:", mevcut_siniflar)
                gosterilecek_df = df[df['Sınıf'] == secili_sinif]
                ekran_dosya_adi = f"{secili_sinif.replace('/', '_')}_Proje_Raporu.xlsx"
            else:
                gosterilecek_df = df
                secili_sinif    = None
                ekran_dosya_adi = "Tum_Siniflar_Proje_Raporu.xlsx"

            gosterilecek_sutunlar = ['Sınıf', 'Okul No', 'Öğrenci Adı Soyadı']
            for k in KRITERLER:
                gosterilecek_sutunlar.append(f"{k['baslik']} Puanı")
            gosterilecek_sutunlar.append('Toplam Puan')

            temiz_df = gosterilecek_df[[col for col in gosterilecek_sutunlar if col in gosterilecek_df.columns]].copy()
            for k in KRITERLER:
                cn = f"{k['baslik']} Puanı"
                if cn in temiz_df.columns:
                    temiz_df[cn] = pd.to_numeric(temiz_df[cn], errors='coerce')
            if 'Toplam Puan' in temiz_df.columns:
                temiz_df['Toplam Puan'] = pd.to_numeric(temiz_df['Toplam Puan'], errors='coerce')

            st.dataframe(temiz_df, use_container_width=True)

            st.markdown("#### 📥 İndirme ve Yazdırma Seçenekleri")
            col_ind1, col_ind2, col_ind3 = st.columns(3)

            with col_ind1:
                output1 = io.BytesIO()
                with pd.ExcelWriter(output1, engine='xlsxwriter') as writer:
                    gosterilecek_df.to_excel(writer, index=False, sheet_name='Rapor')
                st.download_button(
                    label=f"🟢 Excel İndir ({filtre_tipi})",
                    data=output1.getvalue(),
                    file_name=ekran_dosya_adi,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_ind2:
                output2 = io.BytesIO()
                with pd.ExcelWriter(output2, engine='xlsxwriter') as writer:
                    for s in mevcut_siniflar:
                        sinif_df = df[df['Sınıf'] == s]
                        sinif_df.to_excel(writer, index=False, sheet_name=s.replace('/', '_'))
                st.download_button(
                    label="📑 Tüm Sınıfları Tek Excel'de İndir",
                    data=output2.getvalue(),
                    file_name="Tum_Siniflar_Ayri_Sayfalar.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_ind3:
                if filtre_tipi == "Sınıf Bazlı (Tek Sınıf)":
                    html_dosya = toplu_karne_html_dosyasi_uret(gosterilecek_df)
                    st.download_button(
                        label="🖨️ Seçili Sınıfı PDF (Yazdır) Olarak İndir",
                        data=html_dosya,
                        file_name=f"{secili_sinif.replace('/', '_')}_Karneler.html",
                        mime="text/html",
                        use_container_width=True,
                        help="İndirdiğiniz dosyayı tarayıcıda açın. Ctrl+P → PDF olarak kaydedip WhatsApp'tan velilere gönderin."
                    )
                else:
                    st.info("Toplu karne yazdırmak için 'Sınıf Bazlı' filtrelemeyi seçiniz.")

            # YENİ: sınıf bazlı ortalama bar grafiği
            if filtre_tipi == "Tüm Sınıflar (Toplu)":
                st.markdown("---")
                st.markdown("#### 📈 Sınıf Bazlı Puan Ortalamaları")
                ort_df = (
                    df.groupby('Sınıf')['Toplam Puan']
                    .apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
                    .reset_index()
                )
                ort_df.columns = ['Sınıf', 'Ortalama']
                ort_df = ort_df.dropna().sort_values('Sınıf')
                if not ort_df.empty:
                    st.bar_chart(ort_df.set_index('Sınıf'))


# ==========================================
# ANA ÇALIŞTIRMA BLOĞU
# ==========================================
def main():
    tab1, tab2 = st.tabs(["👨‍🎓 Öğrenci Girişi (Karne Arayüzü)", "👨‍🏫 Öğretmen Yönetim Paneli"])
    df = veri_yukle()
    with tab1:
        ogrenci_paneli(df)
    with tab2:
        ogretmen_paneli(df)

if __name__ == "__main__":
    main()
