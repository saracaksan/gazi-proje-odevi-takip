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
# 2. GİZLİ KASA (SECRETS) VE API BAĞLANTILARI
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
except Exception:
    st.error("⚠️ HATA: GEMINI_API_KEY gizli kasada (secrets) bulunamadı!")
    st.stop()

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip()
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"⚠️ HATA: Supabase bilgileri gizli kasada bulunamadı veya yanlış! Detay: {e}")
    st.stop()

# E-posta gönderici (opsiyonel)
EMAIL_SENDER = "saracaksan@gmail.com"
try:
    EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")
except Exception:
    EMAIL_PASSWORD = ""

# ==========================================
# 3. GLOBAL CSS - MOBİL UYUMLU, PROFESYONEL
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* === TEMEL === */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: #f0f4f8;
    color: #0f172a;
}
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

/* === HERO HEADER === */
.hero-header {
    background: linear-gradient(135deg, #0f2d6b 0%, #1e56c7 60%, #3b82f6 100%);
    border-radius: 16px;
    padding: 22px 30px;
    text-align: center;
    box-shadow: 0 8px 30px rgba(30, 58, 138, 0.2);
    margin-bottom: 18px;
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
    background: radial-gradient(circle at 70% 50%, rgba(255,255,255,0.06) 0%, transparent 60%);
}
.hero-title {
    font-family: 'Nunito', sans-serif;
    font-size: clamp(1.4rem, 4vw, 2.2rem);
    font-weight: 900;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: clamp(0.85rem, 2.5vw, 1rem);
    color: #bfdbfe;
    margin-top: 5px;
    font-weight: 600;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    color: white;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    margin-top: 8px;
    font-weight: 700;
}

/* === KARTLAR === */
.glass-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.glass-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }

.stat-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    border-left: 5px solid #2563eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 12px;
}
.stat-card.green { border-left-color: #10b981; }
.stat-card.orange { border-left-color: #f59e0b; }
.stat-card.red { border-left-color: #ef4444; }
.stat-number { font-size: 2rem; font-weight: 900; color: #0f172a; line-height: 1; }
.stat-label { font-size: 0.8rem; color: #64748b; font-weight: 600; margin-top: 4px; }

/* === SECTION HEADER === */
.section-header {
    color: #1e40af;
    font-weight: 800;
    font-size: 1.1rem;
    margin-bottom: 15px;
    border-bottom: 2px solid #bfdbfe;
    padding-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* === BUTONLAR === */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s !important;
    letter-spacing: 0.2px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 6px 20px rgba(5, 150, 105, 0.35) !important;
}

/* === TABS === */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #e2e8f0;
    border-radius: 10px;
    padding: 4px;
    gap: 3px;
    flex-wrap: wrap;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent;
    border-radius: 7px;
    font-weight: 700;
    color: #475569;
    font-size: clamp(0.72rem, 2vw, 0.85rem);
    padding: 6px 10px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #2563eb !important;
    color: white !important;
}

/* === KULLANICI KARTLARI (Okul/Öğretmen navigasyon) === */
.okul-kart {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.okul-kart:hover { border-color: #2563eb; background: #eff6ff; }
.okul-kart.selected { border-color: #2563eb; background: #eff6ff; }

.ogretmen-kart {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.15s;
}
.ogretmen-kart:hover { background: #eff6ff; border-color: #93c5fd; }

/* === BANNER MESAJLARI === */
.info-banner {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    color: #1e40af;
    font-weight: 600;
    font-size: 0.9rem;
}
.warn-banner {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    color: #92400e;
    font-weight: 600;
}
.success-banner {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    color: #166534;
    font-weight: 600;
}

/* === PUAN ROZET === */
.puan-rozet {
    display: inline-block;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 800;
    font-size: 1rem;
}
.puan-rozet.iyı { background: linear-gradient(135deg, #059669, #10b981); }
.puan-rozet.orta { background: linear-gradient(135deg, #d97706, #f59e0b); }
.puan-rozet.dusuk { background: linear-gradient(135deg, #dc2626, #ef4444); }

/* === PROFIL HEADER === */
.profil-bar {
    background: white;
    padding: 14px 22px;
    border-radius: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 18px;
    border-left: 5px solid #2563eb;
    flex-wrap: wrap;
    gap: 10px;
}

/* === FOOTER === */
.app-footer {
    background: #0f172a;
    color: #94a3b8;
    border-radius: 12px;
    padding: 20px 30px;
    margin-top: 30px;
    text-align: center;
    font-size: 0.85rem;
}
.app-footer a { color: #60a5fa; text-decoration: none; }
.app-footer .footer-title { color: white; font-weight: 700; font-size: 1rem; margin-bottom: 6px; }

/* === MOBİL OPTİMİZASYON === */
@media (max-width: 768px) {
    .block-container { padding: 0.5rem !important; }
    .glass-card { padding: 14px; }
    .profil-bar { flex-direction: column; align-items: flex-start; }
    [data-testid="stTabs"] [data-baseweb="tab"] { font-size: 0.7rem; padding: 5px 8px !important; }
}

/* === KILAVUZ ACCORDION === */
.kilavuz-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.kilavuz-baslik {
    font-weight: 700;
    color: #1e40af;
    margin-bottom: 8px;
    font-size: 1rem;
}
.kilavuz-icerik {
    color: #475569;
    font-size: 0.9rem;
    line-height: 1.7;
}

/* === FORM STYLE === */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius: 8px !important;
    border: 1.5px solid #e2e8f0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER
# ==========================================
DARGEÇIT_OKULLARI = [
    "Alayurt İlkokulu", "Alayurt Ortaokulu", "Altınoluk İlkokulu", "Altıyol İlkokulu",
    "Altıyol İmam Hatip Ortaokulu", "Anadolu Kız İmam Hatip Lisesi", "Atatürk Ortaokulu",
    "Bostanlı İlkokulu", "Cumhuriyet İlkokulu", "Dargeçit Anadolu İmam Hatip Lisesi",
    "Dargeçit Anadolu Lisesi", "Dargeçit Ilısu Anadolu Lisesi", "Dargeçit İmam Hatip Ortaokulu",
    "Dargeçit Yunus Emre İlkokulu", "Gazi Ortaokulu", "Ilısu İlkokulu", "Ilısu İlk-Ortaokulu",
    "Karabayır İlkokulu", "Karabayır İlkokulu İHO", "Kartalkaya İlkokulu", "Kılavuz İlkokulu",
    "Kılavuz Ortaokulu", "Nizamülmülk MTAL", "Sakarya İlkokulu", "Selahaddin Eyyubi İlkokulu",
    "Selahaddin Eyyubi İlkokulu/İHO", "Suçatı İlkokulu", "Suçatı İlkokulu - İmam Hatip Ortaokulu",
    "Süleyman Altınkaynak Ortaokulu", "Sümer Beldesi İstiklal İlkokulu", "Sümer İlkokulu",
    "Sümer İmam Hatip Ortaokulu", "Tavşanlı İlkokulu", "Tavşanlı İlkokulu İHO", "Temelli İlkokulu",
    "Temelli İlkokulu/Ortaokulu", "Vatan İlkokulu", "Yılmaz İlkokulu", "Yoncalı İlkokulu",
    "Yoncalı İlkokulu-İmam Hatip Ortaokulu"
]

CEKIRDEK_SABLON = [
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi ve konu hakimiyeti."},
    {"id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli bir şekilde hazırlanmış olması."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler veya açıklamalar."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi."},
    {"id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte teslim edilmesi."}
]

SABLON_ADI = "PROJE DEĞERLENDİRME ÖLÇEĞİ (Varsayılan)"
GEREKLI_SUTUNLAR = [
    'Okul', 'Ekleyen', 'Atanan_Ogretmen', 'Ders', 'Okul No',
    'Öğrenci Adı Soyadı', 'Sınıf', 'Gorev_Turu', 'Gorev_Adi',
    'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON'
]

# ==========================================
# 5. VERİTABANI YÖNETİMİ
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
            if "sistem_kilitli" not in data:
                data["sistem_kilitli"] = False
            if "otomatik_onay" not in data:
                data["otomatik_onay"] = True
            for k, v in data.get("kullanicilar", {}).items():
                if "onayli" not in v:
                    v["onayli"] = True
                if "eposta" not in v:
                    v["eposta"] = ""
            return data
        else:
            varsayilan = {
                "okullar": DARGEÇIT_OKULLARI.copy(),
                "sablonlar": {SABLON_ADI: CEKIRDEK_SABLON},
                "kullanicilar": {
                    "admin": {
                        "sifre": "Sarac.47",
                        "rol": "admin",
                        "ad": "Sistem Yöneticisi",
                        "brans": "Tüm Dersler",
                        "okul": "",
                        "eposta": "saracaksan@gmail.com",
                        "onayli": True
                    }
                },
                "sistem_kilitli": False,
                "otomatik_onay": True
            }
            supabase.table('ayarlar').insert({'id': 1, 'veri': varsayilan}).execute()
            return varsayilan
    except Exception as e:
        st.error(f"Sistem ayarları yüklenemedi: {e}")
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
            'okul': 'Okul', 'ekleyen': 'Ekleyen', 'atanan_ogretmen': 'Atanan_Ogretmen',
            'ders': 'Ders', 'okul_no': 'Okul No', 'ogrenci_adi_soyadi': 'Öğrenci Adı Soyadı',
            'sinif': 'Sınıf', 'gorev_turu': 'Gorev_Turu', 'gorev_adi': 'Gorev_Adi',
            'toplam_puan': 'Toplam Puan', 'genel_degerlendirme_yorumu': 'Genel Değerlendirme Yorumu',
            'dinamik_json': 'Dinamik_JSON'
        }, inplace=True)
        if 'Dinamik_JSON' in df.columns:
            df['Dinamik_JSON'] = df['Dinamik_JSON'].apply(
                lambda x: json.dumps(x) if isinstance(x, dict) else x
            )
        return df
    except Exception as e:
        return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

# ==========================================
# 6. E-POSTA İŞLEMLERİ
# ==========================================
def sifre_olustur(uzunluk=10):
    alfabe = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabe) for _ in range(uzunluk))

def eposta_gonder(alici, konu, icerik):
    """Gmail SMTP ile e-posta gönderir. EMAIL_PASSWORD secrets'ta tanımlı olmalı."""
    if not EMAIL_PASSWORD:
        return False, "E-posta şifresi (EMAIL_PASSWORD) secrets'ta tanımlı değil."
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu
        msg['From'] = EMAIL_SENDER
        msg['To'] = alici
        html_icerik = f"""
        <html><body style="font-family: Arial, sans-serif; background: #f0f4f8; padding: 20px;">
        <div style="background: white; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto; 
             border-top: 5px solid #2563eb; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h2 style="color: #1e3a8a; margin-top: 0;">🧭 PUSULA 360</h2>
            <p style="color: #334155; line-height: 1.6;">{icerik}</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #94a3b8; font-size: 0.85rem;">Dargeçit İlçe Milli Eğitim Müdürlüğü<br>
            Bu e-posta otomatik gönderilmiştir.</p>
        </div></body></html>
        """
        msg.attach(MIMEText(html_icerik, 'html', 'utf-8'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, alici, msg.as_string())
        server.quit()
        return True, "E-posta gönderildi."
    except Exception as e:
        return False, str(e)

# ==========================================
# 7. YARDIMCI FONKSİYONLAR
# ==========================================
def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Listesi')
        writer.sheets['Ogrenci_Listesi'].set_column(0, 2, 25)
    return output.getvalue()

def eokul_sablon_olustur():
    sablon_df = pd.DataFrame(columns=[
        'Öğrenci No', 'Adı Soyadı', 'Sınıfı', 'TÜRKÇE', 'MATEMATİK', 'HAYAT BİLGİSİ',
        'FEN BİLİMLERİ', 'SOSYAL BİLGİLER', 'İNGİLİZCE', 'DİN KÜLTÜRÜ VE AHLAK BİLGİSİ',
        'GÖRSEL SANATLAR', 'MÜZİK', 'BEDEN EĞİTİMİ VE SPOR', 'Davranış Notu'
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='E_Okul_Karne_Listesi')
    return output.getvalue()

def puan_renk(puan):
    try:
        p = int(puan)
        if p >= 85: return "iyi"
        elif p >= 65: return "orta"
        else: return "dusuk"
    except:
        return ""

# ==========================================
# 8. HTML RAPOR OLUŞTURUCU
# ==========================================
def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = """<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Değerlendirme Raporu</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap');
  body { font-family: 'Plus Jakarta Sans', Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }
  .page {
    background: white; width: 100%; max-width: 750px; margin: 0 auto 24px;
    padding: 20px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    page-break-after: always; border-top: 7px solid #2563eb;
  }
  table { width: 100%; border-collapse: collapse; margin-top: 18px; }
  th { background: #f1f5f9; color: #1e293b; padding: 11px; text-align: left; font-size: 0.85rem; border-bottom: 2px solid #cbd5e1; }
  td { padding: 11px; border-bottom: 1px solid #e2e8f0; font-size: 0.88rem; line-height: 1.5; color: #334155; }
  .header { background: linear-gradient(135deg, #0f2d6b, #2563eb); color: white; padding: 18px 22px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { margin: 0; font-size: 1.2rem; }
  .info-box { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 14px; padding: 14px; background: #eff6ff; border-radius: 10px; border-left: 4px solid #3b82f6; }
  .info-item { display: flex; flex-direction: column; }
  .info-label { font-size: 0.72rem; color: #64748b; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
  .info-value { font-size: 1rem; font-weight: 800; color: #0f172a; }
  .yorum { background: #fffbeb; padding: 14px; margin-top: 18px; border-radius: 10px; border-left: 5px solid #f59e0b; color: #78350f; font-size: 0.92rem; line-height: 1.65; }
  .puan-daire { font-size: 2rem; font-weight: 900; background: white; color: #2563eb; padding: 4px 18px; border-radius: 10px; }
  .imza { text-align: right; margin-top: 24px; color: #475569; padding-top: 12px; border-top: 1px dashed #cbd5e1; }
  @media print { .page { box-shadow: none; page-break-after: always; } }
  @media (max-width: 600px) { .header { flex-direction: column; gap: 10px; } }
</style></head><body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam = int(pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce')) if pd.notna(b.get('Toplam Puan', 0)) else 0
        dinamik = json.loads(str(b.get('Dinamik_JSON', '{}'))) if pd.notna(b.get('Dinamik_JSON', '{}')) else {}

        html += f"""
<div class="page">
  <div class="header">
    <div>
      <div style="opacity:0.8; font-size:0.85rem;">{b.get('Okul', '')}</div>
      <h1>{b.get('Gorev_Adi', 'Değerlendirme')} ({b.get('Ders', ogrt_brans)})</h1>
    </div>
    <div style="text-align:center;">
      <div class="puan-daire">{toplam}</div>
      <div style="font-size:0.7rem; margin-top:4px; font-weight:700;">/ 100 PUAN</div>
    </div>
  </div>
  <div class="info-box">
    <div class="info-item"><span class="info-label">Öğrenci</span><span class="info-value">{b.get('Öğrenci Adı Soyadı','')}</span></div>
    <div class="info-item"><span class="info-label">Sınıf</span><span class="info-value">{b.get('Sınıf','')}</span></div>
    <div class="info-item"><span class="info-label">Okul No</span><span class="info-value">{b.get('Okul No','')}</span></div>
    <div class="info-item"><span class="info-label">Görev Türü</span><span class="info-value">{b.get('Gorev_Turu','')}</span></div>
  </div>
  <table>
    <tr><th style="width:26%">Kriter</th><th style="text-align:center;width:9%">Maks</th><th style="text-align:center;width:9%">Alınan</th><th>Açıklama</th></tr>"""

        for k in aktif_kriterler:
            p = dinamik.get(f"{k['id']}_puan", 0)
            a = dinamik.get(f"{k['id']}_aciklama", "-")
            html += f"<tr><td><strong>{k.get('icon','')} {k['baslik']}</strong></td><td style='text-align:center;'>{k['max']}</td><td style='text-align:center; font-weight:800; color:#2563eb;'>{p}</td><td>{a}</td></tr>"

        html += f"""
  </table>
  <div class="yorum"><strong>💬 Genel Yorum:</strong><br><br>{b.get('Genel Değerlendirme Yorumu', 'Değerlendirme bekleniyor.')}</div>
  <div class="imza"><strong>{ogrt_ad}</strong><br>{b.get('Ders', ogrt_brans)} Öğretmeni</div>
</div>"""

    html += "</body></html>"
    return html

# ==========================================
# 9. ANALİZ VE RAPOR FONKSİYONLARI
# ==========================================
def sinif_analiz_raporu(df_sinif, sinif_adi, ogrt_ad):
    """Sınıf bazlı detaylı HTML analiz raporu"""
    df_p = df_sinif.dropna(subset=['Toplam Puan'])
    df_p['Toplam Puan'] = pd.to_numeric(df_p['Toplam Puan'], errors='coerce').fillna(0)

    ortalama = round(df_p['Toplam Puan'].mean(), 1) if len(df_p) > 0 else 0
    en_yuksek = int(df_p['Toplam Puan'].max()) if len(df_p) > 0 else 0
    en_dusuk = int(df_p['Toplam Puan'].min()) if len(df_p) > 0 else 0
    puan_0 = len(df_p[df_p['Toplam Puan'] == 0])
    puan_plus = len(df_p[df_p['Toplam Puan'] > 0])
    yukarida = len(df_p[df_p['Toplam Puan'] >= 85])
    orta_grp = len(df_p[(df_p['Toplam Puan'] >= 65) & (df_p['Toplam Puan'] < 85)])
    asagida = len(df_p[df_p['Toplam Puan'] < 65])

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sinif_adi} Analiz Raporu</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #0f2d6b, #2563eb); color: white; padding: 25px 30px; border-radius: 14px; margin-bottom: 20px; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 20px; }}
  .stat-box {{ background: white; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .stat-num {{ font-size: 2.2rem; font-weight: 900; }}
  .stat-lbl {{ font-size: 0.8rem; color: #64748b; font-weight: 600; }}
  .bar-section {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .bar-label {{ width: 180px; font-size: 0.85rem; font-weight: 600; color: #334155; }}
  .bar-track {{ flex: 1; background: #e2e8f0; border-radius: 6px; height: 22px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 6px; display: flex; align-items: center; padding-left: 8px; color: white; font-size: 0.78rem; font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  th {{ background: #1e3a8a; color: white; padding: 12px; text-align: left; font-size: 0.85rem; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 0.88rem; }}
  tr:hover td {{ background: #f8fafc; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.78rem; font-weight: 700; }}
  .badge-g {{ background: #d1fae5; color: #065f46; }}
  .badge-o {{ background: #fef9c3; color: #854d0e; }}
  .badge-k {{ background: #fee2e2; color: #991b1b; }}
  .footer {{ text-align: center; color: #94a3b8; font-size: 0.82rem; margin-top: 20px; padding: 16px; background: white; border-radius: 10px; }}
</style></head><body><div class="container">
<div class="header">
  <h1 style="margin:0; font-size:1.6rem;">{sinif_adi} — Değerlendirme Analiz Raporu</h1>
  <p style="margin:5px 0 0; opacity:0.85;">Öğretmen: {ogrt_ad} &nbsp;|&nbsp; Oluşturma: {time.strftime('%d.%m.%Y %H:%M')}</p>
</div>
<div class="stats-grid">
  <div class="stat-box"><div class="stat-num" style="color:#2563eb;">{len(df_sinif)}</div><div class="stat-lbl">Toplam Öğrenci</div></div>
  <div class="stat-box"><div class="stat-num" style="color:#10b981;">{ortalama}</div><div class="stat-lbl">Sınıf Ortalaması</div></div>
  <div class="stat-box"><div class="stat-num" style="color:#059669;">{en_yuksek}</div><div class="stat-lbl">En Yüksek Puan</div></div>
  <div class="stat-box"><div class="stat-num" style="color:#ef4444;">{en_dusuk}</div><div class="stat-lbl">En Düşük Puan</div></div>
  <div class="stat-box"><div class="stat-num" style="color:#f59e0b;">{puan_0}</div><div class="stat-lbl">Değerlendirilmemiş</div></div>
</div>
<div class="bar-section">
  <h3 style="margin-top:0; color:#1e3a8a;">Başarı Dağılımı</h3>"""

    toplam_degerlendirilen = max(1, puan_plus)
    html += f"""
  <div class="bar-row">
    <div class="bar-label">🟢 Başarılı (85+)</div>
    <div class="bar-track"><div class="bar-fill" style="width:{round(yukarida/toplam_degerlendirilen*100)}%; background:#10b981;">{yukarida} öğrenci</div></div>
  </div>
  <div class="bar-row">
    <div class="bar-label">🟡 Orta (65-84)</div>
    <div class="bar-track"><div class="bar-fill" style="width:{round(orta_grp/toplam_degerlendirilen*100)}%; background:#f59e0b;">{orta_grp} öğrenci</div></div>
  </div>
  <div class="bar-row">
    <div class="bar-label">🔴 Gelişmeli (&lt;65)</div>
    <div class="bar-track"><div class="bar-fill" style="width:{round(asagida/toplam_degerlendirilen*100)}%; background:#ef4444;">{asagida} öğrenci</div></div>
  </div>
</div>
<table>
<tr><th>#</th><th>Okul No</th><th>Öğrenci Adı Soyadı</th><th>Sınıf</th><th>Görev</th><th>Puan</th><th>Durum</th></tr>"""

    df_sorted = df_sinif.copy()
    df_sorted['Toplam Puan'] = pd.to_numeric(df_sorted['Toplam Puan'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values('Toplam Puan', ascending=False)

    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        p = int(row.get('Toplam Puan', 0))
        badge = 'badge-g' if p >= 85 else ('badge-o' if p >= 65 else 'badge-k')
        durum = 'Başarılı' if p >= 85 else ('Orta' if p >= 65 else ('Gelişmeli' if p > 0 else 'Bekliyor'))
        html += f"<tr><td>{i}</td><td>{row.get('Okul No','')}</td><td><strong>{row.get('Öğrenci Adı Soyadı','')}</strong></td><td>{row.get('Sınıf','')}</td><td>{row.get('Gorev_Adi','')}</td><td style='font-weight:800;'>{p}</td><td><span class='badge {badge}'>{durum}</span></td></tr>"

    html += f"""</table>
<div class="footer">PUSULA 360 Bütüncül Değerlendirme Platformu &nbsp;|&nbsp; {time.strftime('%d.%m.%Y')}<br>
Tasarım: Sıraç AKSAN — <a href="mailto:saracaksan@gmail.com" style="color:#2563eb;">saracaksan@gmail.com</a></div>
</div></body></html>"""
    return html

# ==========================================
# 10. YAPAY ZEKA BAĞLANTILARI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye = "".join(filter(str.isdigit, sinif_str)) or "7"
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])
    prompt = f"""Sen profesyonel bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}. {seviye}. Sınıf öğrencisi değerlendiriyorsun.
Öğrenciyle doğrudan 'sen' diliyle şefkatli ve motive edici konuş.
Değerlendirme Kriterleri:\n{kriter_ozeti}\nGÖREV MODU: """
    if mod == "A":
        prompt += f"""YORUMDAN PUAN ÜRETME. Öğretmenin notu: "{ham_metin}"\nBu nota göre pedagojik açıklamalar yaz ve mantıklı puanlar belirle."""
    elif mod == "B":
        prompt += f"""HEDEF PUANDAN YORUM ÜRETME. Hedef: {hedef_puan}/100\nBu puana ulaşacak şekilde kriterlere puan dağıt ve açıklamalar yaz."""
    else:
        ozet = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA. Öğretmen puanları verdi:\n{ozet}\nSadece pedagojik açıklamalar yaz. PUANLARI DEĞİŞTİRME."""
    prompt += """\nEKSTRA: "genel" anahtarında motive edici genel yorum yaz.
SADECE JSON:\n{ "puanlar": { "k1": 40 }, "aciklamalar": { "k1": "..." }, "genel": "..." }"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw.replace('```json', '').replace('```', '').strip())

def ai_karne_gorusu_yaz(ogrenci_adi, sinifi, notlar_sozlugu, davranis_notu, ogrt_ad):
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu)])
    prompt = f"""Sınıf öğretmeni {ogrt_ad} olarak {sinifi} sınıfından {ogrenci_adi} adlı öğrenciye e-okul karne görüşü yaz.
Ders Notları:\n{notlar_metni}\nGözlem: {davranis_notu}
Pedagojik, doğrudan öğrenciye hitap eden 3-4 cümlelik metin üret. Türkçe."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "text/plain"}
    }
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ==========================================
# 11. ÖĞRENCİ SORGULAMA EKRANI
# ==========================================
def ogrenci_sorgu_ekrani(df):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔍 Öğrenci Performans Sorgulama</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    okul_listesi = sorted(df['Okul'].dropna().unique().tolist()) if not df.empty else []
    s_okul = col1.selectbox("🏫 Okulunuz", ["— Okul Seçiniz —"] + okul_listesi)

    sinif_listesi = sorted(df[df['Okul'] == s_okul]['Sınıf'].dropna().unique().tolist()) if s_okul != "— Okul Seçiniz —" else []
    s_sinif = col2.selectbox("📚 Sınıfınız", ["— Sınıf —"] + sinif_listesi if sinif_listesi else ["Önce okul seçin"])

    s_no = st.text_input("🔢 Okul Numaranız", placeholder="Okul numaranızı girin...")

    if st.button("🔍 Sonuçlarımı Getir", use_container_width=True):
        if s_okul == "— Okul Seçiniz —" or not s_no.strip():
            st.warning("Lütfen okul ve okul numaranızı girin.")
        else:
            filtre = (df['Okul'] == s_okul) & (df['Okul No'] == s_no.strip())
            if s_sinif not in ["— Sınıf —", "Önce okul seçin"]:
                filtre = filtre & (df['Sınıf'] == s_sinif)
            sonuclar = df[filtre]

            if sonuclar.empty:
                st.error("❌ Bu bilgilerle kayıt bulunamadı.")
            else:
                ogrenci_adi = sonuclar.iloc[0]['Öğrenci Adı Soyadı']
                st.markdown(f"""
                <div class="success-banner">
                    👋 Hoş geldin, <strong>{ogrenci_adi}</strong>! 
                    Sistemde <strong>{len(sonuclar)}</strong> görev kaydın bulunuyor.
                </div>
                """, unsafe_allow_html=True)

                for _, row in sonuclar.iterrows():
                    toplam_val = pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')
p = int(toplam_val) if pd.notna(toplam_val) else 0
        renk_cls = puan_renk(p)
                    with st.expander(f"📌 {row['Gorev_Adi']} ({row['Ders']}) — Puan: {p}/100"):
                        st.markdown(f"""
                        <div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:12px;">
                            <div><strong>Görev Türü:</strong> {row.get('Gorev_Turu','')}</div>
                            <div><strong>Sınıf:</strong> {row.get('Sınıf','')}</div>
                            <div><strong>Okul:</strong> {row.get('Okul','')}</div>
                        </div>
                        <div><span class="puan-rozet {renk_cls}">{p} / 100</span></div>
                        """, unsafe_allow_html=True)

                        if row.get('Genel Değerlendirme Yorumu'):
                            st.markdown(f"""
                            <div class="warn-banner" style="margin-top:10px;">
                                💬 <strong>Öğretmen Yorumu:</strong><br>{row['Genel Değerlendirme Yorumu']}
                            </div>
                            """, unsafe_allow_html=True)

                        # Kriter detayları
                        dinamik = {}
                        try:
                            if pd.notna(row.get('Dinamik_JSON', '')):
                                dinamik = json.loads(str(row['Dinamik_JSON']))
                        except:
                            pass
                        if dinamik:
                            st.markdown("**📊 Kriter Puanları:**")
                            for k in CEKIRDEK_SABLON:
                                kp = dinamik.get(f"{k['id']}_puan", 0)
                                ka = dinamik.get(f"{k['id']}_aciklama", "")
                                if kp or ka:
                                    st.markdown(f"- {k.get('icon','')} **{k['baslik']}**: {kp}/{k['max']} — {ka}")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 12. GİRİŞ EKRANI
# ==========================================
def giris_ekrani(df, ayarlar):
    tab_ogr, tab_ogrt = st.tabs(["🎓 Öğrenci Sorgulama", "👨‍🏫 Öğretmen / İdare Girişi"])

    with tab_ogr:
        ogrenci_sorgu_ekrani(df)

    with tab_ogrt:
        c1, c2, c3 = st.columns([1, 1.8, 1])
        with c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            g1, g2, g3 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol", "🔑 Şifremi Unuttum"])

            # GİRİŞ
            with g1:
                if ayarlar.get("sistem_kilitli", False):
                    st.warning("🔒 Sistem öğretmen girişine kapatılmıştır.")
                k_adi = st.text_input("Kullanıcı Adı", key="l_kadi")
                sifre = st.text_input("Şifre", type="password", key="l_sifre")
                if st.button("Giriş Yap →", use_container_width=True, key="btn_giris"):
                    user = ayarlar["kullanicilar"].get(k_adi)
                    if user and user["sifre"] == sifre:
                        if user.get("rol") != "admin" and not user.get("onayli", True):
                            st.warning("⏳ Hesabınız yönetici onayı bekliyor.")
                        elif ayarlar.get("sistem_kilitli", False) and user.get("rol") != "admin":
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

            # KAYIT OL
            with g2:
                r_okul = st.selectbox("Okulunuz", ayarlar["okullar"], key="r_okul")
                r_ad = st.text_input("Ad Soyad", key="r_ad")
                r_brans = st.text_input("Branş", key="r_brans")
                r_eposta = st.text_input("E-posta Adresiniz", key="r_eposta", placeholder="ornek@gmail.com")
                r_kadi = st.text_input("Kullanıcı Adı Seçin", key="r_kadi")
                r_sifre = st.text_input("Şifre Belirleyin", type="password", key="r_sifre")
                if st.button("Kayıt Ol", use_container_width=True, key="btn_kayit"):
                    if r_kadi in ayarlar["kullanicilar"]:
                        st.error("Bu kullanıcı adı alınmış.")
                    elif not (r_kadi and r_sifre and r_ad):
                        st.warning("Lütfen tüm alanları doldurun.")
                    else:
                        is_auto = ayarlar.get("otomatik_onay", True)
                        ayarlar["kullanicilar"][r_kadi] = {
                            "sifre": r_sifre, "rol": "ogretmen", "ad": r_ad,
                            "okul": r_okul, "brans": r_brans, "eposta": r_eposta, "onayli": is_auto
                        }
                        ayar_kaydet(ayarlar)
                        if is_auto:
                            st.success("✅ Kayıt başarılı! Giriş yapabilirsiniz.")
                        else:
                            st.success("⏳ Kayıt alındı. Yönetici onayından sonra giriş yapabilirsiniz.")

            # ŞİFREMİ UNUTTUM
            with g3:
                st.markdown("E-posta adresinize yeni şifre gönderilecektir.")
                u_eposta = st.text_input("Kayıtlı E-posta Adresiniz", key="u_eposta")
                if st.button("🔑 Yeni Şifre Gönder", use_container_width=True, key="btn_sifre"):
                    bulunan = None
                    bulunan_kadi = None
                    for kadi, user in ayarlar["kullanicilar"].items():
                        if user.get("eposta", "").strip().lower() == u_eposta.strip().lower():
                            bulunan = user
                            bulunan_kadi = kadi
                            break
                    if not bulunan:
                        st.error("Bu e-posta ile kayıtlı kullanıcı bulunamadı.")
                    else:
                        yeni_sifre = sifre_olustur()
                        ok, mesaj = eposta_gonder(
                            u_eposta,
                            "PUSULA 360 – Yeni Şifreniz",
                            f"Sayın {bulunan['ad']},<br><br>"
                            f"Şifre yenileme talebiniz alındı. Yeni şifreniz: <strong>{yeni_sifre}</strong><br><br>"
                            f"Giriş yaptıktan sonra profilinizden şifrenizi değiştirebilirsiniz."
                        )
                        if ok:
                            ayarlar["kullanicilar"][bulunan_kadi]["sifre"] = yeni_sifre
                            ayar_kaydet(ayarlar)
                            st.success(f"✅ Yeni şifre {u_eposta} adresine gönderildi.")
                        else:
                            st.error(f"E-posta gönderilemedi: {mesaj}")
                            st.info(f"Manuel şifre: **{yeni_sifre}** (Yöneticiye iletin)")
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 13. KULLANIM KILAVUZU
# ==========================================
def kullanim_kilavuzu():
    with st.expander("📖 PUSULA 360 Kullanım Kılavuzu — Tıkla, Aç", expanded=False):
        st.markdown("""
        <div class="kilavuz-item">
        <div class="kilavuz-baslik">1️⃣ Sisteme Kayıt ve Giriş</div>
        <div class="kilavuz-icerik">
        • <b>Kayıt Ol</b> sekmesinden okul, ad-soyad, branş ve e-posta bilgilerinizi girerek kayıt olun.<br>
        • Yönetici otomatik onayı açmışsa direkt giriş yapabilirsiniz; kapalıysa yönetici onayını bekleyin.<br>
        • Şifrenizi unutursanız <b>"Şifremi Unuttum"</b> sekmesinden e-posta ile yeni şifre alabilirsiniz.
        </div></div>

        <div class="kilavuz-item">
        <div class="kilavuz-baslik">2️⃣ Öğrenci Listesi Yükleme</div>
        <div class="kilavuz-icerik">
        • <b>Öğrenci & Görev İşlemleri → Excel ile Toplu Yükle</b> sekmesinden örnek Excel şablonunu indirin.<br>
        • Şablonu doldurun: <b>Okul No</b>, <b>Ad Soyad</b>, <b>Sınıf</b> sütunları zorunludur.<br>
        • Okul numaralarının sıra numarası değil gerçek okul numarası olduğuna dikkat edin.<br>
        • Görev türünü (Proje/Performans) ve görevin adını belirleyip yükleyin.
        </div></div>

        <div class="kilavuz-item">
        <div class="kilavuz-baslik">3️⃣ Yapay Zeka Değerlendirme</div>
        <div class="kilavuz-icerik">
        • <b>AI Değerlendirme</b> sekmesinde öğrenci ve görevi seçin.<br>
        • <b>Mod A:</b> Sadece bir not/yorum yazın, AI puanları otomatik dağıtsın.<br>
        • <b>Mod B:</b> Vermek istediğiniz toplam puanı girin, AI geri kalanı yapsın.<br>
        • <b>Mod C:</b> Puanları kendiniz verin, AI sadece edebi açıklamalar yazsın.<br>
        • Sonuçları gözden geçirip <b>Kaydet</b> butonuyla veritabanına yazın.
        </div></div>

        <div class="kilavuz-item">
        <div class="kilavuz-baslik">4️⃣ Raporlar ve Çıktılar</div>
        <div class="kilavuz-icerik">
        • <b>Raporlar</b> sekmesinde sınıf seçerek hem kişisel karneleri hem de sınıf analiz raporunu indirebilirsiniz.<br>
        • HTML karneler tarayıcıda açılıp Ctrl+P ile PDF'e dönüştürülebilir.<br>
        • Excel çizelgeleri e-okul sistemine aktarıma uygundur.
        </div></div>

        <div class="kilavuz-item">
        <div class="kilavuz-baslik">5️⃣ Veri Silme ve Yedekleme</div>
        <div class="kilavuz-icerik">
        • <b>Silme İşlemleri</b> sekmesinden tek tek kayıt silebilirsiniz.<br>
        • <b>Toplu Silme</b> ile tüm bir sınıfın veya okuldaki tüm verileri temizleyebilirsiniz.<br>
        • <b>Raporlar → Veri Yedekleme</b> ile tüm verilerinizi Excel olarak bilgisayarınıza indirin.<br>
        • <b>Dikkat:</b> Silme işlemi geri alınamaz! Önce yedek alın.
        </div></div>

        <div class="kilavuz-item">
        <div class="kilavuz-baslik">6️⃣ E-Okul Karne Görüşü</div>
        <div class="kilavuz-icerik">
        • <b>E-Okul Karne</b> sekmesinde örnek şablonu indirip öğrenci notlarını doldurun.<br>
        • Her öğrenci için AI ile 3-4 cümlelik pedagojik görüş oluşturun, düzenleyin ve onaylayın.<br>
        • Tamamlanan listeyi Excel olarak indirip e-okul sistemine aktarın.
        </div></div>

        <div class="kilavuz-item">
        <div class="kilavuz-baslik">7️⃣ Yönetici (Admin) Özellikleri</div>
        <div class="kilavuz-icerik">
        • Tüm okulların ve öğretmenlerin verilerini görüntüleyip yönetebilirsiniz.<br>
        • <b>Öğretmen Navigasyonu:</b> Okul seçin → Öğretmen seçin → Detay bilgilere erişin.<br>
        • <b>Gözatma Modu:</b> Öğretmen üzerine tıklayarak onun gördüğü ekrana geçebilirsiniz.<br>
        • Kullanıcı onaylama, şifre sıfırlama, okul ekleme/silme ve şablon yönetimi yapabilirsiniz.
        </div></div>
        """, unsafe_allow_html=True)

# ==========================================
# 14. YÖNETİM PANELİ
# ==========================================
def yonetim_paneli(df, ayarlar):
    aktif_id = st.session_state["aktif_kullanici"]
    kb = st.session_state["kullanici_bilgi"]
    rol = kb["rol"]
    admin_bakis = st.session_state.get("admin_bakis_modu", False)
    admin_bakis_ogrt = st.session_state.get("admin_bakis_ogretmen", None)

    # Profil bar
    col_profil1, col_profil2 = st.columns([3, 1])
    with col_profil1:
        st.markdown(f"""
        <div class="profil-bar">
            <div>
                <div style="font-size:1.2rem; font-weight:900; color:#1e293b;">
                    {'👁️ Gözatma: ' if admin_bakis else '👋 '}{kb['ad']}
                    {f'<span style="background:#fef9c3;color:#854d0e;padding:2px 8px;border-radius:6px;font-size:0.75rem;margin-left:8px;">ADMİN GÖZATMA → {admin_bakis_ogrt}</span>' if admin_bakis else ''}
                </div>
                <div style="font-size:0.9rem; color:#64748b; font-weight:600;">
                    {kb.get('okul','') or 'Yönetici'} &nbsp;|&nbsp; {kb.get('brans','')}
                    {'&nbsp;|&nbsp; <span style="color:#ef4444;">🔴 ADMİN</span>' if rol == 'admin' and not admin_bakis else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_profil2:
        if admin_bakis:
            if st.button("← Admin'e Dön"):
                st.session_state["admin_bakis_modu"] = False
                st.session_state["admin_bakis_ogretmen"] = None
                st.rerun()
        else:
            if st.button("🚪 Çıkış Yap"):
                st.session_state.clear()
                st.rerun()

    # Hangi öğretmenin gözüyle bakıyoruz?
    if admin_bakis and admin_bakis_ogrt:
        kb_bakis = ayarlar["kullanicilar"].get(admin_bakis_ogrt, kb)
        df_yetkili = df[
            (df['Okul'] == kb_bakis.get("okul")) &
            ((df['Atanan_Ogretmen'] == admin_bakis_ogrt) | (df['Atanan_Ogretmen'] == 'admin'))
        ]
    elif rol == "admin":
        df_yetkili = df
    else:
        df_yetkili = df[
            (df['Okul'] == kb.get("okul")) &
            ((df['Atanan_Ogretmen'] == aktif_id) | (df['Atanan_Ogretmen'] == 'admin'))
        ]

    kullanim_kilavuzu()

    # SEKME YAPISI
    if rol == "admin" and not admin_bakis:
        sekme_basliklari = [
            "👥 Öğrenci & Görev", "🤖 AI Değerlendirme",
            "📊 Raporlar", "📝 E-Okul Karne",
            "👨‍🏫 Öğretmen Yönetimi", "⚙️ Sistem Ayarları"
        ]
    else:
        sekme_basliklari = [
            "👥 Öğrenci & Görev", "🤖 AI Değerlendirme",
            "📊 Raporlar", "📝 E-Okul Karne", "⚙️ Profilim"
        ]

    sekmeler = st.tabs(sekme_basliklari)

    # ============ SEKME 0: ÖĞRENCİ & GÖREV YÖNETİMİ ============
    with sekmeler[0]:
        t1, t2, t3, t4 = st.tabs([
            "📥 Excel ile Yükle", "➕ Tekil Ekle",
            "🏫 Havuzdan Görev Ata", "🗑️ Silme İşlemleri"
        ])

        # --- Excel yükleme ---
        with t1:
            st.markdown("<div class='section-header'>📥 Excel ile Toplu Görev Tanımla</div>", unsafe_allow_html=True)
            h_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul Seçin", ayarlar["okullar"], key="ex_okul")

            hedef_ogrt_ex = aktif_id
            kb_aktif = kb if not admin_bakis else ayarlar["kullanicilar"].get(admin_bakis_ogrt, kb)

            if rol == "admin" and not admin_bakis:
                ogrt_listesi = {k: f"{v['ad']} ({v.get('brans','-')})" for k, v in ayarlar["kullanicilar"].items()
                                if v.get("rol") == "ogretmen" and v.get("okul") == h_okul and v.get("onayli", True)}
                if ogrt_listesi:
                    hedef_ogrt_ex = st.selectbox(
                        "Atanacak Öğretmen", ["admin"] + list(ogrt_listesi.keys()),
                        format_func=lambda x: "Yönetici" if x == "admin" else ogrt_listesi[x]
                    )
                else:
                    st.warning("Bu okulda öğretmen yok. Görev yöneticiye atanacak.")
                    hedef_ogrt_ex = "admin"

            g_tur = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"])
            g_isim = st.text_input("Görevin Adı", placeholder="Örn: Dönem Sonu Fen Projesi")

            col_dl, col_up = st.columns([1, 2])
            col_dl.download_button("📄 Örnek Şablon İndir", data=bos_sablon_olustur(), file_name="Ogrenci_Sablon.xlsx")
            uploaded_file = col_up.file_uploader("Excel Listesi Yükle", type=['xlsx'])

            if st.button("🚀 Listeyi Yükle ve Görevi Ata", use_container_width=True):
                if not uploaded_file:
                    st.error("❌ Excel dosyasını yükleyin!")
                elif not g_isim.strip():
                    st.error("❌ Görev adını girin!")
                else:
                    try:
                        excel_df = pd.read_excel(uploaded_file, dtype={"Okul No": str})
                        no_col = next((c for c in excel_df.columns if "no" in str(c).lower()), excel_df.columns[0])
                        ad_col = next((c for c in excel_df.columns if "ad" in str(c).lower()), excel_df.columns[1])
                        sinif_col = next((c for c in excel_df.columns if "sınıf" in str(c).lower() or "sinif" in str(c).lower()),
                                         excel_df.columns[2] if len(excel_df.columns) > 2 else None)

                        excel_df.dropna(subset=[no_col], inplace=True)
                        excel_df[no_col] = excel_df[no_col].astype(str).str.strip().str.replace('.0', '', regex=False)

                        db_records = []
                        for _, row in excel_df.iterrows():
                            o_no = row[no_col]
                            kontrol = df[(df['Okul'] == h_okul) & (df['Okul No'] == o_no) &
                                         (df['Gorev_Adi'] == g_isim.strip()) & (df['Atanan_Ogretmen'] == hedef_ogrt_ex)]
                            if kontrol.empty:
                                target_ders = (kb_aktif.get("brans", "Genel") if hedef_ogrt_ex == aktif_id
                                               else ayarlar["kullanicilar"].get(hedef_ogrt_ex, {}).get("brans", "Genel"))
                                sinif_val = str(row[sinif_col]) if sinif_col and sinif_col in row else "Bilinmiyor"
                                db_records.append({
                                    'okul': h_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': hedef_ogrt_ex,
                                    'ders': target_ders, 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col],
                                    'sinif': sinif_val, 'gorev_turu': g_tur, 'gorev_adi': g_isim.strip(), 'dinamik_json': {}
                                })

                        if db_records:
                            supabase.table('gorevler').insert(db_records).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(db_records)} öğrenciye '{g_isim}' görevi tanımlandı!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("Tüm öğrenciler için bu görev zaten atanmış.")
                    except Exception as e:
                        st.error(f"Hata: {e}")

        # --- Tekil ekle ---
        with t2:
            st.markdown("<div class='section-header'>➕ Tekil Öğrenci/Görev Ekle</div>", unsafe_allow_html=True)
            with st.form("tekil_ekle"):
                m_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul", ayarlar["okullar"])
                hedef_ogrt_man = aktif_id
                if rol == "admin" and not admin_bakis:
                    ogrt_listesi_man = {k: f"{v['ad']} ({v.get('okul','-')})" for k, v in ayarlar["kullanicilar"].items()
                                        if v.get("rol") == "ogretmen" and v.get("onayli", True)}
                    hedef_ogrt_man = st.selectbox(
                        "Öğretmen", ["admin"] + list(ogrt_listesi_man.keys()),
                        format_func=lambda x: "Yönetici" if x == "admin" else ogrt_listesi_man[x]
                    )
                col_m1, col_m2, col_m3 = st.columns(3)
                m_no = col_m1.text_input("Okul No")
                m_ad = col_m2.text_input("Ad Soyad")
                m_sinif = col_m3.text_input("Sınıf")
                m_gtur = st.selectbox("Görev Türü", ["Proje", "Performans"])
                m_gadi = st.text_input("Görev Adı")
                if st.form_submit_button("➕ Ekle ve Kaydet"):
                    if m_no and m_ad and m_gadi:
                        target_ders_man = (kb.get("brans", "") if hedef_ogrt_man == aktif_id
                                           else ayarlar["kullanicilar"].get(hedef_ogrt_man, {}).get("brans", ""))
                        supabase.table('gorevler').insert({
                            'okul': m_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': hedef_ogrt_man,
                            'ders': target_ders_man, 'okul_no': m_no.strip(), 'ogrenci_adi_soyadi': m_ad,
                            'sinif': m_sinif, 'gorev_turu': m_gtur, 'gorev_adi': m_gadi, 'dinamik_json': {}
                        }).execute()
                        st.cache_data.clear()
                        st.success("✅ Eklendi!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Okul no, ad ve görev adı zorunludur.")

        # --- Havuzdan görev ata ---
        with t3:
            st.markdown("<div class='section-header'>🏫 Havuzdaki Sınıflara Yeni Görev Ata</div>", unsafe_allow_html=True)
            st.markdown('<div class="info-banner">Okulunuzdaki diğer öğretmenlerin yüklediği sınıfları seçerek kendi dersiniz için görev tanımlayabilirsiniz.</div>', unsafe_allow_html=True)

            islem_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul", ayarlar["okullar"], key="havuz_okul")

            mevcut_siniflar = sorted(df[df['Okul'] == islem_okul]['Sınıf'].dropna().unique().tolist()) if not df.empty else []
            if mevcut_siniflar:
                secilen_siniflar = st.multiselect("Görev Atanacak Sınıflar", mevcut_siniflar)

                h_ogrt = aktif_id
                if rol == "admin" and not admin_bakis:
                    ogrt_list_h = {k: f"{v['ad']} ({v.get('brans','-')})" for k, v in ayarlar["kullanicilar"].items()
                                   if v.get("rol") == "ogretmen" and v.get("okul") == islem_okul and v.get("onayli", True)}
                    if ogrt_list_h:
                        h_ogrt = st.selectbox("Görevi Veren Öğretmen", ["admin"] + list(ogrt_list_h.keys()),
                                              format_func=lambda x: "Yönetici" if x == "admin" else ogrt_list_h[x])

                g_tur_h = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"], key="gth")
                g_isim_h = st.text_input("Görevin Adı", key="gih", placeholder="Örn: Matematik Dönem Projesi")

                if st.button("🚀 Seçili Sınıflara Görevi Ata", use_container_width=True):
                    if not secilen_siniflar or not g_isim_h.strip():
                        st.error("Sınıf seçin ve görev adı girin.")
                    else:
                        pool_students = df[(df['Okul'] == islem_okul) & (df['Sınıf'].isin(secilen_siniflar))].drop_duplicates(subset=['Okul No'])
                        db_records_h = []
                        for _, row in pool_students.iterrows():
                            o_no = row['Okul No']
                            kontrol = df[(df['Okul'] == islem_okul) & (df['Okul No'] == o_no) &
                                         (df['Gorev_Adi'] == g_isim_h.strip()) & (df['Atanan_Ogretmen'] == h_ogrt)]
                            if kontrol.empty:
                                t_ders = (kb.get("brans", "Genel") if h_ogrt == aktif_id
                                          else ayarlar["kullanicilar"].get(h_ogrt, {}).get("brans", "Genel"))
                                db_records_h.append({
                                    'okul': islem_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': h_ogrt,
                                    'ders': t_ders, 'okul_no': o_no, 'ogrenci_adi_soyadi': row['Öğrenci Adı Soyadı'],
                                    'sinif': row['Sınıf'], 'gorev_turu': g_tur_h, 'gorev_adi': g_isim_h.strip(), 'dinamik_json': {}
                                })
                        if db_records_h:
                            supabase.table('gorevler').insert(db_records_h).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(db_records_h)} öğrenciye görev atandı!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("Bu görev zaten atanmış.")
            else:
                st.info("Bu okula ait öğrenci kaydı yok. Önce Excel ile yükleme yapın.")

        # --- Silme işlemleri ---
        with t4:
            st.markdown("<div class='section-header'>🗑️ Veri Silme İşlemleri</div>", unsafe_allow_html=True)
            st.markdown('<div class="warn-banner">⚠️ Silme işlemleri geri alınamaz! Önemli verileri silmeden önce <b>Raporlar → Veri Yedekleme</b> bölümünden yedek alın.</div>', unsafe_allow_html=True)

            sil_t1, sil_t2, sil_t3 = st.tabs(["📌 Tekil Kayıt Sil", "🏫 Sınıf Toplu Sil", "🏢 Okul Toplu Sil"])

            with sil_t1:
                if not df_yetkili.empty:
                    s_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                    silinecek = st.selectbox("Silinecek Kayıt", ["— Seçiniz —"] + s_liste)
                    if st.button("🗑️ Bu Kaydı Sil") and silinecek != "— Seçiniz —":
                        o_no = silinecek.split(" - ")[0].strip()
                        g_ad = silinecek.split(" | ")[1].strip()
                        supabase.table('gorevler').delete().eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                        st.cache_data.clear()
                        st.success("Silindi.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("Silecek kayıt yok.")

            with sil_t2:
                sil_okul2 = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul", ayarlar["okullar"], key="sil_okul2")
                mevcut_siniflar_sil = sorted(df[df['Okul'] == sil_okul2]['Sınıf'].dropna().unique().tolist()) if not df.empty else []
                if mevcut_siniflar_sil:
                    secilen_sinif_sil = st.multiselect("Silinecek Sınıflar (Tüm görevleri silinecek)", mevcut_siniflar_sil)
                    secilen_gorev_sil = st.selectbox("Sadece Bu Görev (Opsiyonel — Boş bırakırsan tümü)",
                                                      ["Tüm Görevler"] + sorted(df[df['Okul'] == sil_okul2]['Gorev_Adi'].dropna().unique().tolist()))
                    if secilen_sinif_sil:
                        kac = len(df[(df['Okul'] == sil_okul2) & (df['Sınıf'].isin(secilen_sinif_sil))])
                        st.warning(f"Bu işlem {kac} kaydı silecek!")
                        onay = st.checkbox(f"Evet, {kac} kaydı silmek istiyorum — bunu anlıyorum.")
                        if onay and st.button("🗑️ Sınıf Verilerini Sil", type="primary"):
                            q = supabase.table('gorevler').delete().eq('okul', sil_okul2).in_('sinif', secilen_sinif_sil)
                            if secilen_gorev_sil != "Tüm Görevler":
                                q = supabase.table('gorevler').delete().eq('okul', sil_okul2).in_('sinif', secilen_sinif_sil).eq('gorev_adi', secilen_gorev_sil)
                            q.execute()
                            st.cache_data.clear()
                            st.success(f"✅ Silindi.")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.info("Bu okulda sınıf verisi yok.")

            with sil_t3:
                if rol != "admin":
                    st.error("Bu işlem sadece yöneticiler tarafından yapılabilir.")
                else:
                    sil_okul3 = st.selectbox("Tüm Verileri Silinecek Okul", ayarlar["okullar"], key="sil_okul3")
                    kac3 = len(df[df['Okul'] == sil_okul3]) if not df.empty else 0
                    if kac3 > 0:
                        st.error(f"⛔ Bu işlem {sil_okul3} okuluna ait TÜM {kac3} kaydı silecek!")
                        onay3 = st.checkbox(f"Evet, {sil_okul3} okulunun tüm {kac3} kaydını siliyorum, anlıyorum.")
                        if onay3 and st.button("⛔ Okul Verilerini Komple Sil", type="primary"):
                            supabase.table('gorevler').delete().eq('okul', sil_okul3).execute()
                            st.cache_data.clear()
                            st.success("Silindi.")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info("Bu okulda kayıt yok.")

    # ============ SEKME 1: AI DEĞERLENDİRME ============
    with sekmeler[1]:
        st.markdown("<div class='section-header'>🤖 Yapay Zeka Destekli Puanlama</div>", unsafe_allow_html=True)
        if df_yetkili.empty:
            st.warning("Değerlendirilecek görev bulunamadı.")
        else:
            c_sec1, c_sec2 = st.columns([2, 1])
            puan_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
            secili_gorev = c_sec1.selectbox("🎯 Öğrenci ve Görevi Seçin", ["— Seçiniz —"] + puan_liste)
            s_isimler = list(ayarlar.get("sablonlar", {}).keys())
            sec_sablon_ismi = c_sec2.selectbox("📋 Şablon", s_isimler)
            aktif_sablon = ayarlar["sablonlar"].get(sec_sablon_ismi, CEKIRDEK_SABLON)

            if secili_gorev != "— Seçiniz —":
                o_no = secili_gorev.split(" - ")[0].strip()
                g_ad = secili_gorev.split(" | ")[1].strip()
                idx_list = df[(df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_ad)].index
                if len(idx_list) == 0:
                    st.error("Kayıt bulunamadı.")
                else:
                    idx = idx_list[0]
                    bilgi = df.iloc[idx]

                    if st.session_state.get("aktif_idx") != idx:
                        st.session_state["aktif_idx"] = idx
                        e_puanlar = {}
                        try:
                            if pd.notna(bilgi.get('Dinamik_JSON', '')):
                                e_puanlar = json.loads(str(bilgi['Dinamik_JSON']))
                        except:
                            pass
                        for k in aktif_sablon:
                            st.session_state[f"vp_{k['id']}"] = int(e_puanlar.get(f"{k['id']}_puan", 0))
                            st.session_state[f"va_{k['id']}"] = str(e_puanlar.get(f"{k['id']}_aciklama", ""))
                        st.session_state["vg"] = str(bilgi.get('Genel Değerlendirme Yorumu', ""))

                    st.markdown(f"""
                    <div style="background:#eff6ff; padding:14px; border-radius:10px; border-left:4px solid #3b82f6; margin-bottom:14px;">
                        <strong>{bilgi.get('Öğrenci Adı Soyadı','')}</strong> &nbsp;|&nbsp; 
                        {bilgi.get('Sınıf','')} &nbsp;|&nbsp; 
                        {bilgi.get('Gorev_Adi','')} &nbsp;|&nbsp; 
                        No: {bilgi.get('Okul No','')}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="glass-card" style="background:#fafafa;">', unsafe_allow_html=True)
                    ai_modu = st.radio(
                        "🤖 AI Modu:",
                        ["A", "B", "C"],
                        format_func=lambda x: {
                            "A": "📝 Mod A — Yorum Gir, AI Puanlasın",
                            "B": "🎯 Mod B — Hedef Puan Ver, AI Dağıtsın",
                            "C": "✋ Mod C — Manuel Puan, AI Açıklasın"
                        }[x],
                        horizontal=True
                    )
                    ham_metin, hedef_puan = "", 85
                    if ai_modu == "A":
                        ham_metin = st.text_area("Öğretmen notunuz:", placeholder="Öğrenci projeyi zamanında teslim etti, içerik yeterliydi...")
                    elif ai_modu == "B":
                        hedef_puan = st.slider("Hedef Puan", 0, 100, 85)
                    if st.button("✨ Yapay Zekayı Çalıştır", use_container_width=True):
                        with st.spinner("Yapay zeka analiz ediyor..."):
                            try:
                                m_p_d = {k['id']: st.session_state.get(f"vp_{k['id']}", 0) for k in aktif_sablon}
                                res = ai_degerlendirme_yap(
                                    bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan,
                                    m_p_d, kb.get("ad", ""), bilgi['Ders']
                                )
                                for k in aktif_sablon:
                                    if k['id'] in res.get("puanlar", {}):
                                        st.session_state[f"vp_{k['id']}"] = int(res["puanlar"][k['id']])
                                    if k['id'] in res.get("aciklamalar", {}):
                                        st.session_state[f"va_{k['id']}"] = res["aciklamalar"][k['id']]
                                if "genel" in res:
                                    st.session_state["vg"] = res["genel"]
                                st.success("✅ Değerlendirme hazır! Aşağıdan kontrol edip kaydedin.")
                            except Exception as e:
                                st.error(f"AI hatası: {e}")
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("#### 📝 Puanlama Formu")
                    with st.form("kayit_formu"):
                        toplam_h = 0
                        for k in aktif_sablon:
                            st.markdown(f"""
                            <div style='background:#f0f9ff; padding:10px 14px; border-radius:8px; border-left:4px solid #2563eb; margin-bottom:8px;'>
                                <strong style='color:#1e3a8a;'>{k.get('icon','📌')} {k['baslik']}</strong> 
                                <span style='color:#64748b; font-size:0.85rem;'>(Max: {k['max']} puan)</span><br>
                                <em style='color:#94a3b8; font-size:0.82rem;'>{k['aciklama']}</em>
                            </div>
                            """, unsafe_allow_html=True)
                            cc1, cc2 = st.columns([1, 3])
                            pv = cc1.number_input(f"Puan (0-{k['max']})", 0, k['max'], key=f"vp_{k['id']}", label_visibility="collapsed")
                            av = cc2.text_area("Açıklama", key=f"va_{k['id']}", height=65, label_visibility="collapsed")
                            toplam_h += pv
                        gv = st.text_area("💬 Genel Yorum", key="vg", height=90)
                        st.markdown(f"""<div style='background:#f0fdf4; padding:12px; border-radius:8px; border-left:4px solid #10b981; font-size:1.1rem; font-weight:800;'>
                        Toplam: <span style='color:#059669;'>{toplam_h} / 100</span></div>""", unsafe_allow_html=True)
                        if st.form_submit_button("💾 Veritabanına Kaydet", use_container_width=True):
                            d_k_flat = {}
                            for k in aktif_sablon:
                                d_k_flat.update({
                                    f"{k['id']}_puan": st.session_state[f"vp_{k['id']}"],
                                    f"{k['id']}_aciklama": st.session_state[f"va_{k['id']}"]
                                })
                            supabase.table('gorevler').update({
                                'dinamik_json': d_k_flat,
                                'genel_degerlendirme_yorumu': gv,
                                'toplam_puan': toplam_h
                            }).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                            st.cache_data.clear()
                            st.success("✅ Kalıcı olarak kaydedildi!")
                            time.sleep(1)
                            st.rerun()

    # ============ SEKME 2: RAPORLAR ============
    with sekmeler[2]:
        st.markdown("<div class='section-header'>📊 Rapor ve Belge Çıktıları</div>", unsafe_allow_html=True)
        if not df_yetkili.empty:
            c_r1, c_r2 = st.columns([1, 1])
            r_sinif = c_r1.selectbox("Sınıf Seçin", ["Tümü"] + sorted(df_yetkili['Sınıf'].dropna().unique()))
            df_r = df_yetkili if r_sinif == "Tümü" else df_yetkili[df_yetkili['Sınıf'] == r_sinif]

            g_filtre = c_r2.selectbox("Görev Filtrele", ["Tümü"] + sorted(df_r['Gorev_Adi'].dropna().unique().tolist()))
            if g_filtre != "Tümü":
                df_r = df_r[df_r['Gorev_Adi'] == g_filtre]

            # İstatistik kartları
            if not df_r.empty:
                df_r_copy = df_r.copy()
                df_r_copy['Toplam Puan'] = pd.to_numeric(df_r_copy['Toplam Puan'], errors='coerce').fillna(0)
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                col_s1.markdown(f'<div class="stat-card"><div class="stat-number">{len(df_r_copy)}</div><div class="stat-label">Toplam Kayıt</div></div>', unsafe_allow_html=True)
                col_s2.markdown(f'<div class="stat-card green"><div class="stat-number">{round(df_r_copy["Toplam Puan"].mean(),1)}</div><div class="stat-label">Ortalama</div></div>', unsafe_allow_html=True)
                col_s3.markdown(f'<div class="stat-card orange"><div class="stat-number">{int(df_r_copy["Toplam Puan"].max())}</div><div class="stat-label">En Yüksek</div></div>', unsafe_allow_html=True)
                col_s4.markdown(f'<div class="stat-card red"><div class="stat-number">{len(df_r_copy[df_r_copy["Toplam Puan"]==0])}</div><div class="stat-label">Değerlendirilmemiş</div></div>', unsafe_allow_html=True)

            st.dataframe(
                df_r[['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan']].sort_values('Toplam Puan', ascending=False),
                use_container_width=True, hide_index=True
            )

            c_btn1, c_btn2, c_btn3 = st.columns(3)

            # Excel çizelgesi
            out_xls = io.BytesIO()
            with pd.ExcelWriter(out_xls, engine='xlsxwriter') as writer:
                df_r[['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan']].to_excel(writer, index=False, sheet_name='Cizelge')
            c_btn1.download_button("📊 Excel Çizelgesi", data=out_xls.getvalue(), file_name=f"{r_sinif}_Cizelge.xlsx", use_container_width=True)

            # HTML Karneler
            if c_btn2.button("🖨️ Kişisel Karneler (HTML)", use_container_width=True):
                s_aktif = ayarlar["sablonlar"].get(list(ayarlar["sablonlar"].keys())[0], CEKIRDEK_SABLON)
                h_cikti = toplu_karne_html_dosyasi_uret(df_r, kb.get("ad", ""), kb.get("brans", ""), s_aktif)
                st.download_button("📥 HTML Karneleri İndir", data=h_cikti, file_name=f"{r_sinif}_Karneler.html", mime="text/html", use_container_width=True)

            # Sınıf analiz raporu
            if c_btn3.button("📈 Sınıf Analiz Raporu (HTML)", use_container_width=True):
                analiz_html = sinif_analiz_raporu(df_r, r_sinif, kb.get("ad", ""))
                st.download_button("📥 Analiz Raporunu İndir", data=analiz_html, file_name=f"{r_sinif}_Analiz.html", mime="text/html", use_container_width=True)

            st.markdown("---")
            st.markdown("#### 💾 Veri Yedekleme")
            col_y1, col_y2 = st.columns(2)
            out_yedek = io.BytesIO()
            with pd.ExcelWriter(out_yedek, engine='xlsxwriter') as writer:
                df_yetkili.to_excel(writer, index=False, sheet_name='Verilerim')
            col_y1.download_button(
                "📥 Kendi Verilerimi Yedekle",
                data=out_yedek.getvalue(),
                file_name=f"Yedek_{time.strftime('%Y%m%d_%H%M')}.xlsx",
                use_container_width=True
            )

            if rol == "admin":
                out_tam = io.BytesIO()
                with pd.ExcelWriter(out_tam, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sistem_Yedek')
                col_y2.download_button(
                    "📥 Tüm Sistemi Yedekle (Admin)",
                    data=out_tam.getvalue(),
                    file_name=f"SistemYedek_{time.strftime('%Y%m%d_%H%M')}.xlsx",
                    use_container_width=True
                )
        else:
            st.info("Rapor oluşturmak için veri bulunamadı.")

    # ============ SEKME 3: E-OKUL KARNE ============
    with sekmeler[3]:
        st.markdown("<div class='section-header'>📝 E-Okul Karne Görüşü Yazıcı</div>", unsafe_allow_html=True)
        st.download_button("📄 Örnek Not Şablonu İndir", data=eokul_sablon_olustur(), file_name="Eokul_Sablon.xlsx")
        k_dosya = st.file_uploader("Öğrenci Not Listesini Yükle (Excel/CSV)", type=['xlsx', 'csv', 'xls'])

        if k_dosya:
            if "kdf" not in st.session_state or st.session_state.get("last_k_file") != k_dosya.name:
                try:
                    if k_dosya.name.endswith('.csv'):
                        kdf = pd.read_csv(k_dosya, sep=None, engine='python')
                    else:
                        kdf = pd.read_excel(k_dosya)
                    if "AI_Karne_Gorusu" not in kdf.columns:
                        kdf["AI_Karne_Gorusu"] = ""
                    st.session_state["kdf"] = kdf
                    st.session_state["last_k_file"] = k_dosya.name
                except Exception as e:
                    st.error(f"Dosya okuma hatası: {e}")

        if "kdf" in st.session_state:
            kdf = st.session_state["kdf"]
            cols = kdf.columns.tolist()
            c_ad = next((c for c in cols if "ad" in str(c).lower() and "soyad" in str(c).lower()), cols[1] if len(cols) > 1 else cols[0])
            c_sinif = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols) > 2 else cols[0])
            not_cols = [c for c in cols if c not in [c_ad, c_sinif, cols[0], "AI_Karne_Gorusu", "Davranış Notu"]]

            c_k1, c_k2 = st.columns([1, 2])
            o_sec_k = c_k1.selectbox("Öğrenci Seç", kdf[c_ad].tolist())
            o_idx_k = kdf[kdf[c_ad] == o_sec_k].index[0]

            davranis = ""
            if "Davranış Notu" in kdf.columns and pd.notna(kdf.loc[o_idx_k, "Davranış Notu"]):
                davranis = str(kdf.loc[o_idx_k, "Davranış Notu"])
            obs = c_k1.text_area("Öğretmen Gözlemi (Opsiyonel)", value=davranis)

            if c_k1.button("✨ Görüş Üret", use_container_width=True):
                with st.spinner("AI cümleler oluşturuyor..."):
                    try:
                        n_dict = {d: kdf.loc[o_idx_k, d] for d in not_cols}
                        g_metin = ai_karne_gorusu_yaz(kdf.loc[o_idx_k, c_ad], kdf.loc[o_idx_k, c_sinif], n_dict, obs, kb.get("ad", ""))
                        st.session_state["kdf"].at[o_idx_k, "AI_Karne_Gorusu"] = g_metin
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")

            y_gorus = c_k2.text_area("Görüşü Düzenle / Onayla", value=kdf.at[o_idx_k, "AI_Karne_Gorusu"], height=150)
            if c_k2.button("💾 Bu Görüşü Onayla ve Kaydet"):
                st.session_state["kdf"].at[o_idx_k, "AI_Karne_Gorusu"] = y_gorus
                st.success("✅ Onaylandı.")

            out_k = io.BytesIO()
            with pd.ExcelWriter(out_k, engine='xlsxwriter') as writer:
                st.session_state["kdf"].to_excel(writer, index=False, sheet_name='Karne_Gorusleri')
            st.download_button("📥 Tamamlanan Listeyi İndir", data=out_k.getvalue(), file_name="E_Okul_Gorusleri.xlsx", use_container_width=True)

    # ============ SEKME 4: ÖĞRETMEN YÖNETİMİ (Admin) ============
    if rol == "admin" and not admin_bakis and len(sekmeler) >= 5:
        with sekmeler[4]:
            st.markdown("<div class='section-header'>👨‍🏫 Öğretmen Yönetimi — Okul › Öğretmen Navigasyonu</div>", unsafe_allow_html=True)

            col_nav1, col_nav2 = st.columns([1, 2])

            with col_nav1:
                st.markdown("#### 🏢 Okullar")
                tum_okullar = sorted(ayarlar["okullar"])
                secili_okul = st.session_state.get("nav_okul", tum_okullar[0] if tum_okullar else "")

                for okul in tum_okullar:
                    o_ogretmen = [v for k, v in ayarlar["kullanicilar"].items() if v.get("okul") == okul and v.get("rol") == "ogretmen"]
                    secili_cls = "selected" if okul == secili_okul else ""
                    if st.button(f"🏫 {okul} ({len(o_ogretmen)} öğretmen)", key=f"okul_{okul}", use_container_width=True):
                        st.session_state["nav_okul"] = okul
                        st.session_state["nav_ogretmen"] = None
                        st.rerun()

            with col_nav2:
                if secili_okul:
                    st.markdown(f"#### 👨‍🏫 {secili_okul} — Öğretmenler")

                    okul_ogretmenler = {k: v for k, v in ayarlar["kullanicilar"].items()
                                        if v.get("okul") == secili_okul and v.get("rol") == "ogretmen"}

                    bekleyenler_okul = [k for k, v in okul_ogretmenler.items() if not v.get("onayli", True)]
                    if bekleyenler_okul:
                        st.markdown(f'<div class="warn-banner">⏳ {len(bekleyenler_okul)} öğretmen onay bekliyor.</div>', unsafe_allow_html=True)

                    if not okul_ogretmenler:
                        st.info("Bu okulda kayıtlı öğretmen yok.")
                    else:
                        for kadi, user in okul_ogretmenler.items():
                            onayli_badge = "✅" if user.get("onayli", True) else "⏳"
                            ogrt_gorev_sayisi = len(df[(df['Okul'] == secili_okul) & (df['Atanan_Ogretmen'] == kadi)])

                            col_ogrt1, col_ogrt2, col_ogrt3 = st.columns([3, 1, 1])
                            col_ogrt1.markdown(f"""
                            <div style="padding:10px; background:#f8fafc; border-radius:8px; border-left:3px solid {'#10b981' if user.get('onayli',True) else '#f59e0b'};">
                                {onayli_badge} <strong>{user['ad']}</strong><br>
                                <span style="color:#64748b; font-size:0.82rem;">{user.get('brans','')} | {ogrt_gorev_sayisi} görev | {user.get('eposta','—')}</span>
                            </div>
                            """, unsafe_allow_html=True)

                            if col_ogrt2.button("👁️ Gözat", key=f"goz_{kadi}"):
                                st.session_state["admin_bakis_modu"] = True
                                st.session_state["admin_bakis_ogretmen"] = kadi
                                st.rerun()

                            if col_ogrt3.button("✏️ Düzenle", key=f"duz_{kadi}"):
                                st.session_state["nav_ogretmen"] = kadi
                                st.rerun()

                        # Öğretmen düzenleme paneli
                        sec_ogrt_duzenle = st.session_state.get("nav_ogretmen")
                        if sec_ogrt_duzenle and sec_ogrt_duzenle in ayarlar["kullanicilar"]:
                            user_d = ayarlar["kullanicilar"][sec_ogrt_duzenle]
                            st.markdown(f"---\n#### ✏️ {user_d['ad']} — Bilgi Düzenleme")

                            col_d1, col_d2 = st.columns(2)
                            with st.form(f"ogrt_duzenle_{sec_ogrt_duzenle}"):
                                y_ad = col_d1.text_input("Ad Soyad", value=user_d['ad'])
                                y_brans = col_d2.text_input("Branş", value=user_d.get('brans', ''))
                                y_okul_idx = ayarlar["okullar"].index(user_d['okul']) if user_d['okul'] in ayarlar["okullar"] else 0
                                y_okul = st.selectbox("Okul", ayarlar["okullar"], index=y_okul_idx)
                                y_eposta = st.text_input("E-posta", value=user_d.get('eposta', ''))
                                y_sifre = st.text_input("Şifre", value=user_d['sifre'], type="password")
                                y_onayli = st.checkbox("Onaylı Hesap", value=user_d.get("onayli", True))

                                col_f1, col_f2 = st.columns(2)
                                guncelle_btn = col_f1.form_submit_button("💾 Güncelle")
                                sil_btn = col_f2.form_submit_button("🗑️ Sil", type="primary")

                                if guncelle_btn:
                                    ayarlar["kullanicilar"][sec_ogrt_duzenle].update({
                                        "ad": y_ad, "okul": y_okul, "brans": y_brans,
                                        "eposta": y_eposta, "sifre": y_sifre, "onayli": y_onayli
                                    })
                                    ayar_kaydet(ayarlar)
                                    st.success("✅ Güncellendi!")
                                    time.sleep(1)
                                    st.rerun()

                                if sil_btn:
                                    del ayarlar["kullanicilar"][sec_ogrt_duzenle]
                                    ayar_kaydet(ayarlar)
                                    st.session_state["nav_ogretmen"] = None
                                    st.rerun()

            st.markdown("---")
            col_ek1, col_ek2 = st.columns(2)

            with col_ek1:
                st.markdown("#### ➕ Yeni Öğretmen Ekle (Manuel)")
                with st.form("manuel_ogrt_ekle"):
                    e_kadi = st.text_input("Kullanıcı Adı")
                    e_ad = st.text_input("Ad Soyad")
                    e_okul = st.selectbox("Okul", ayarlar["okullar"])
                    e_brans = st.text_input("Branş")
                    e_eposta = st.text_input("E-posta")
                    e_sifre = st.text_input("Şifre")
                    if st.form_submit_button("➕ Ekle ve Onayla"):
                        if e_kadi in ayarlar["kullanicilar"]:
                            st.error("Kullanıcı adı mevcut!")
                        elif e_kadi and e_sifre and e_ad:
                            ayarlar["kullanicilar"][e_kadi] = {
                                "sifre": e_sifre, "rol": "ogretmen", "ad": e_ad,
                                "okul": e_okul, "brans": e_brans, "eposta": e_eposta, "onayli": True
                            }
                            ayar_kaydet(ayarlar)
                            st.success("✅ Eklendi!")
                            st.rerun()

            with col_ek2:
                st.markdown("#### ⏳ Onay Bekleyenler")
                oto_onay = st.checkbox("Otomatik Onay Aktif", value=ayarlar.get("otomatik_onay", True))
                if oto_onay != ayarlar.get("otomatik_onay", True):
                    ayarlar["otomatik_onay"] = oto_onay
                    ayar_kaydet(ayarlar)
                    st.rerun()

                bekleyenler_tum = {k: v for k, v in ayarlar["kullanicilar"].items() if not v.get("onayli", True)}
                if bekleyenler_tum:
                    for bk, bv in bekleyenler_tum.items():
                        c1b, c2b, c3b = st.columns([2, 1, 1])
                        c1b.markdown(f"**{bv['ad']}** ({bv.get('okul','')})")
                        if c2b.button("✅", key=f"onay_{bk}"):
                            ayarlar["kullanicilar"][bk]["onayli"] = True
                            ayar_kaydet(ayarlar)
                            st.rerun()
                        if c3b.button("❌", key=f"red_{bk}"):
                            del ayarlar["kullanicilar"][bk]
                            ayar_kaydet(ayarlar)
                            st.rerun()
                else:
                    st.info("Onay bekleyen yok.")

    # ============ SEKME 5: SİSTEM AYARLARI (Admin) veya PROFİL (Öğretmen) ============
    son_sekme_idx = 5 if (rol == "admin" and not admin_bakis) else 4
    with sekmeler[son_sekme_idx]:
        if rol == "admin" and not admin_bakis:
            st.markdown("<div class='section-header'>⚙️ Sistem Ayarları ve Şablon Yönetimi</div>", unsafe_allow_html=True)
            col_ay1, col_ay2 = st.columns(2)

            with col_ay1:
                st.markdown("#### 🔒 Sistem Kontrolü")
                kilitli = st.checkbox("Sistemi Öğretmen Girişine Kapat", value=ayarlar.get("sistem_kilitli", False))
                if kilitli != ayarlar.get("sistem_kilitli", False):
                    ayarlar["sistem_kilitli"] = kilitli
                    ayar_kaydet(ayarlar)
                    st.rerun()

                st.markdown("#### 🏢 Okul Listesi")
                y_okul_ekle = st.text_input("Yeni Okul Adı")
                if st.button("➕ Okul Ekle") and y_okul_ekle:
                    ayarlar["okullar"].append(y_okul_ekle)
                    ayar_kaydet(ayarlar)
                    st.rerun()
                sil_okul = st.selectbox("Okul Sil", ["— Seçiniz —"] + ayarlar["okullar"])
                if st.button("🗑️ Seçili Okulu Sil") and sil_okul != "— Seçiniz —":
                    ayarlar["okullar"].remove(sil_okul)
                    ayar_kaydet(ayarlar)
                    st.rerun()

            with col_ay2:
                st.markdown("#### 📐 Yeni Değerlendirme Şablonu")
                st.info("Kriterlerin puan toplamı 100 olmalıdır.")
                if "t_df" not in st.session_state:
                    st.session_state["t_df"] = pd.DataFrame([{"Başlık": "İçerik", "Puan": 50, "Açıklama": ""}])
                s_isim_yeni = st.text_input("Şablon Adı")
                e_df = st.data_editor(st.session_state["t_df"], num_rows="dynamic", use_container_width=True)
                if st.button("💾 Şablonu Kaydet"):
                    if pd.to_numeric(e_df["Puan"], errors="coerce").sum() == 100 and s_isim_yeni:
                        n_k = [{"id": f"k{i+1}", "baslik": str(r["Başlık"]), "max": int(r["Puan"]), "icon": "📌", "aciklama": str(r["Açıklama"])} for i, r in e_df.iterrows()]
                        ayarlar["sablonlar"][s_isim_yeni] = n_k
                        ayar_kaydet(ayarlar)
                        st.success("✅ Eklendi")
                        st.rerun()
                    else:
                        st.error("Toplam 100 olmalı ve isim girilmeli!")

                st.markdown("#### Şablon Sil")
                sil_sablon = st.selectbox("Silinecek Şablon", list(ayarlar["sablonlar"].keys()))
                if st.button("🗑️ Şablonu Sil"):
                    if "Varsayılan" in sil_sablon:
                        st.error("Varsayılan şablon silinemez!")
                    else:
                        del ayarlar["sablonlar"][sil_sablon]
                        ayar_kaydet(ayarlar)
                        st.rerun()

        else:
            st.markdown("<div class='section-header'>⚙️ Kişisel Profil Ayarları</div>", unsafe_allow_html=True)
            with st.form("profil_form"):
                p_ad = st.text_input("Ad Soyad", value=kb["ad"])
                p_brans = st.text_input("Branş", value=kb.get("brans", ""))
                p_eposta = st.text_input("E-posta Adresiniz", value=kb.get("eposta", ""))
                p_sifre = st.text_input("Yeni Şifre (boş bırakırsan değişmez)", type="password")
                if st.form_submit_button("💾 Bilgilerimi Güncelle"):
                    guncelleme = {"ad": p_ad, "brans": p_brans, "eposta": p_eposta}
                    if p_sifre.strip():
                        guncelleme["sifre"] = p_sifre
                    ayarlar["kullanicilar"][aktif_id].update(guncelleme)
                    ayar_kaydet(ayarlar)
                    st.session_state["kullanici_bilgi"] = ayarlar["kullanicilar"][aktif_id]
                    st.success("✅ Profiliniz güncellendi!")

# ==========================================
# 15. FOOTER
# ==========================================
def footer_goster():
    st.markdown("""
    <div class="app-footer">
        <div class="footer-title">🧭 PUSULA 360 — Bütüncül Değerlendirme Platformu</div>
        <div>Dargeçit İlçe Milli Eğitim Müdürlüğü | Proje, Performans ve Karne Yönetim Sistemi</div>
        <br>
        <div>
            Sistem Tasarımcısı: <strong style="color:white;">Sıraç AKSAN</strong> &nbsp;|&nbsp;
            📧 <a href="mailto:saracaksan@gmail.com">saracaksan@gmail.com</a> &nbsp;|&nbsp;
            📱 0506 928 22 10
        </div>
        <div style="margin-top: 8px; font-size:0.78rem;">
            © 2025 PUSULA 360. Tüm hakları saklıdır. Yazılım Sıraç AKSAN tarafından geliştirilmiştir.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 16. ANA ÇALIŞTIRMA
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df = veri_yukle()

    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🧭 PUSULA 360</div>
        <div class="hero-subtitle">Bütüncül Proje, Performans ve Karne Değerlendirme Platformu</div>
        <span class="hero-badge">Dargeçit İlçe Milli Eğitim Müdürlüğü</span>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("giris_yapti", False):
        giris_ekrani(df, ayarlar)
    else:
        yonetim_paneli(df, ayarlar)

    footer_goster()

if __name__ == "__main__":
    main()
