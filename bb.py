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
    page_title="PROPERKAR360 | Türkiye Geneli Değerlendirme Platformu",
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

EMAIL_SENDER = "properkar360@gmail.com"
try:
    EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")
except Exception:
    EMAIL_PASSWORD = ""

# ==========================================
# 3. GLOBAL CSS — MODERN & CANLI MENÜ TASARIMI
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: #f0f4f8;
    color: #0f172a;
}
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* ── Hero Başlık ── */
.hero-header {
    background: linear-gradient(135deg, #0f2d6b 0%, #1e56c7 60%, #3b82f6 100%);
    border-radius: 16px;
    padding: 22px 30px;
    text-align: center;
    box-shadow: 0 8px 30px rgba(30,58,138,0.25);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
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

/* ── NAVİGASYON (MENÜ) SİSTEMİ ── */
/* Streamlit'in native butonlarını manipüle edip mükemmel menülere dönüştürüyoruz */

.nav-main-wrapper {
    background: #0f172a;
    padding: 12px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    margin-bottom: 12px;
    border-bottom: 4px solid #3b82f6; /* Mavi Çizgi */
}
.nav-sub-wrapper {
    background: #ffffff;
    padding: 12px;
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    border: 1px solid #e2e8f0;
    margin-bottom: 24px;
}

/* Menü Butonları Ortak Özellikleri (El işareti, Canlı Efekt) */
.nav-main-wrapper button, .nav-sub-wrapper button {
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Ana Menü Butonları */
.nav-main-wrapper button {
    background: #1e293b !important;
    color: #94a3b8 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    padding: 12px 10px !important;
}
.nav-main-wrapper button:hover {
    background: #334155 !important;
    color: #ffffff !important;
    transform: translateY(-2px) scale(1.02) !important; /* Pop efekti */
}
.nav-main-wrapper button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; /* Aktif Mavi */
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.4) !important;
    transform: scale(1.03) !important;
}

/* Alt Menü Butonları */
.nav-sub-wrapper button {
    background: #f8fafc !important;
    color: #475569 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important; 
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    padding: 10px !important;
}
.nav-sub-wrapper button:hover {
    background: #d1fae5 !important; /* Hoverda açık yeşil */
    color: #059669 !important;
    border-color: #34d399 !important;
    transform: translateY(-2px) scale(1.02) !important; /* Pop efekti */
}
.nav-sub-wrapper button[kind="primary"] {
    background: linear-gradient(135deg, #059669, #10b981) !important; /* Aktif Yeşil */
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(16,185,129,0.3) !important;
    transform: scale(1.03) !important;
}

/* ── Standart Kart & Paneller ── */
.glass-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.section-header {
    color: #1e40af;
    font-weight: 800;
    font-size: 1.1rem;
    margin-bottom: 16px;
    border-bottom: 2px solid #bfdbfe;
    padding-bottom: 8px;
}

/* ── Bildirim Banner'lar ── */
.info-banner { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #1e40af; font-weight: 600; font-size: 0.9rem; }
.warn-banner { background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #92400e; font-weight: 600; font-size: 0.9rem; }
.success-banner { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #166534; font-weight: 600; font-size: 0.9rem; }

/* ── Puan Rozeti ── */
.puan-rozet { display: inline-block; color: white; padding: 4px 14px; border-radius: 20px; font-weight: 800; font-size: 1rem; }
.puan-rozet.iyi   { background: linear-gradient(135deg, #059669, #10b981); }
.puan-rozet.orta  { background: linear-gradient(135deg, #d97706, #f59e0b); }
.puan-rozet.dusuk { background: linear-gradient(135deg, #dc2626, #ef4444); }

/* ── Profil Çubuğu ── */
.profil-bar { background: white; padding: 14px 22px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; border-left: 5px solid #2563eb; }

/* ── Kılavuz ── */
.kilavuz-item { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; margin-bottom: 8px; }
.kilavuz-baslik  { font-weight: 700; color: #1e40af; margin-bottom: 8px; font-size: 1rem; }

/* ── Form elemanları ── */
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {
    border-radius: 8px !important; border: 1.5px solid #e2e8f0 !important; transition: all 0.2s !important; cursor: pointer;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}

/* ── Footer ── */
.app-footer { background: #0f172a; color: #94a3b8; border-radius: 12px; padding: 22px 30px; margin-top: 32px; text-align: center; font-size: 0.85rem; }
.app-footer .footer-title { color: white; font-weight: 700; font-size: 1rem; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER VE BAŞLANGIÇ VERİLERİ
# ==========================================
TUM_ILLER = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
]

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
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Sorunsuz çözüm, konu hakimiyeti."},
    {"id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Temiz ve okunaklı hazırlık."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Konuyu destekleyen ekstra içerik."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Görsel materyal desteği."},
    {"id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Belirtilen tarihte teslim."}
]

SABLON_ADI = "PROJE DEĞERLENDİRME ÖLÇEĞİ (Varsayılan)"
GEREKLI_SUTUNLAR = [
    'Okul', 'Ekleyen', 'Atanan_Ogretmen', 'Ders', 'Okul No',
    'Öğrenci Adı Soyadı', 'Sınıf', 'Gorev_Turu', 'Gorev_Adi',
    'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON'
]

ALT_MENU_OGR_GOREV = [("excel_yukle", "📥 Excel ile Yükle"), ("tekil_ekle", "➕ Tekil Ekle"), ("havuz_ata", "🏫 Havuzdan Görev Ata"), ("silme", "🗑️ Silme İşlemleri")]
ALT_MENU_RAPORLAR = [("sinif_rapor", "📊 Sınıf Raporları"), ("yedekleme", "💾 Veri Yedekleme")]
ALT_MENU_AYARLAR_ADMIN = [("sistem", "🔒 Sistem"), ("okullar", "🏢 İl/İlçe/Okul Yönetimi"), ("sablonlar", "📐 Ölçek")]
ALT_MENU_AYARLAR_OGRT = [("profil", "👤 Profilim"), ("sablonlar", "📐 Ölçek / Şablon")]
ALT_MENU_SIL = [("tekil_sil", "📌 Tekil Sil"), ("sinif_sil", "🏫 Sınıf Sil"), ("okul_sil", "🏢 Okul Sil")]

# ==========================================
# 5. ÖZEL NAVİGASYON YARDIMCILARI
# ==========================================
def _init_nav():
    if "nav_ana" not in st.session_state: st.session_state["nav_ana"] = "ogr_gorev"
    if "nav_ogr_alt" not in st.session_state: st.session_state["nav_ogr_alt"] = "excel_yukle"
    if "nav_rapor_alt" not in st.session_state: st.session_state["nav_rapor_alt"] = "sinif_rapor"
    if "nav_ayar_alt" not in st.session_state: st.session_state["nav_ayar_alt"] = "profil"
    if "nav_sil_alt" not in st.session_state: st.session_state["nav_sil_alt"] = "tekil_sil"

def render_nav_bar(menu_items: list, state_key: str, is_main: bool = True):
    wrapper_class = "nav-main-wrapper" if is_main else "nav-sub-wrapper"
    st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
    cols = st.columns(len(menu_items))
    aktif = st.session_state.get(state_key, menu_items[0][0])
    
    for col, (key, label) in zip(cols, menu_items):
        is_active = (aktif == key)
        if col.button(label, key=f"navbtn_{state_key}_{key}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state[state_key] = key
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_ana_nav(rol: str, admin_bakis: bool):
    items = [
        ("ogr_gorev", "👥 Öğrenci & Görev"),
        ("ai_degerlendirme", "🤖 AI Değerlendirme"),
        ("raporlar", "📊 Raporlar"),
        ("eokul", "📝 E-Okul Karne"),
    ]
    if rol == "admin" and not admin_bakis:
        items.append(("ogretmen_yonetim", "👨‍🏫 Öğretmen Yönetimi"))
    items.append(("ayarlar", "⚙️ Ayarlar"))
    render_nav_bar(items, "nav_ana", is_main=True)

# ==========================================
# 6. VERİTABANI YÖNETİMİ VE GÖÇ (MIGRATION)
# ==========================================
def ayar_yukle():
    try:
        res = supabase.table('ayarlar').select('veri').eq('id', 1).execute()
        if res.data:
            data = res.data[0]['veri']
            # Veri Göçü (Eski liste yapısını İl -> İlçe -> Okul dict yapısına taşı)
            if "okullar" in data and isinstance(data["okullar"], list):
                eski_liste = data["okullar"]
                data["okullar"] = {"Mardin": {"Dargeçit": eski_liste}}
            elif "okullar" not in data or not data["okullar"]:
                data["okullar"] = {"Mardin": {"Dargeçit": DARGEÇIT_OKULLARI.copy()}}
                
            if "sablonlar" not in data or not data["sablonlar"]:
                data["sablonlar"] = {SABLON_ADI: CEKIRDEK_SABLON}
            if "sistem_kilitli" not in data: data["sistem_kilitli"] = False
            if "otomatik_onay" not in data: data["otomatik_onay"] = True
            
            for k, v in data.get("kullanicilar", {}).items():
                if "onayli" not in v: v["onayli"] = True
                if "eposta" not in v: v["eposta"] = ""
            return data
        else:
            varsayilan = {
                "okullar": {"Mardin": {"Dargeçit": DARGEÇIT_OKULLARI.copy()}},
                "sablonlar": {SABLON_ADI: CEKIRDEK_SABLON},
                "kullanicilar": {
                    "admin": {
                        "sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi",
                        "brans": "", "okul": "", "eposta": "properkar360@gmail.com", "onayli": True
                    }
                },
                "sistem_kilitli": False, "otomatik_onay": True
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
            df['Dinamik_JSON'] = df['Dinamik_JSON'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
        return df
    except Exception as e:
        return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

# ==========================================
# 7. E-POSTA İŞLEMLERİ
# ==========================================
def sifre_olustur(uzunluk=10):
    alfabe = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabe) for _ in range(uzunluk))

def eposta_gonder(alici, konu, icerik):
    if not EMAIL_PASSWORD:
        return False, "E-posta şifresi (EMAIL_PASSWORD) secrets'ta tanımlı değil."
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu
        msg['From'] = EMAIL_SENDER
        msg['To'] = alici
        html_icerik = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f4f8;padding:20px;">
        <div style="background:white;border-radius:12px;padding:30px;max-width:500px; margin:0 auto;border-top:5px solid #2563eb;">
            <h2 style="color:#1e3a8a;margin-top:0;">🧭 PROPERKAR360</h2>
            <p style="color:#334155;line-height:1.6;">{icerik}</p>
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
# 8. YARDIMCI FONKSİYONLAR
# ==========================================
def tum_okul_listesi_duz_getir(okullar_dict):
    liste = []
    for il, ilceler in okullar_dict.items():
        for ilce, okullar in ilceler.items():
            for okul in okullar:
                liste.append(f"{il} / {ilce} / {okul}")
    return sorted(liste)

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
        'GÖRSEL SANATLAR', 'MÜZİK', 'BEDEN EĞİTİMİ VE SPOR', 'Davranış'
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='E_Okul_Karne_Listesi')
    return output.getvalue()

def puan_renk(puan):
    try:
        p = int(puan)
        if p >= 85:   return "iyi"
        elif p >= 65: return "orta"
        else:         return "dusuk"
    except:
        return ""

def kriter_bul(k_id, ayarlar):
    for s_kriterler in ayarlar.get("sablonlar", {}).values():
        for kr in s_kriterler:
            if kr["id"] == k_id: return kr["baslik"], kr["max"], kr.get("icon", "📌")
    for kr in CEKIRDEK_SABLON:
        if kr["id"] == k_id: return kr["baslik"], kr["max"], kr.get("icon", "📌")
    return "Kriter", 100, "📌"

# ==========================================
# 9. HTML RAPOR ŞABLONLARI (Kısaltıldı ama eksiksiz çalışır)
# ==========================================
def ogrenci_karnesi_html_uret(df_ogrenci, ayarlar, tekil_gorev_idx=None):
    df_islem = df_ogrenci.loc[[tekil_gorev_idx]] if tekil_gorev_idx is not None else df_ogrenci
    ogr_ad    = df_ogrenci.iloc[0].get('Öğrenci Adı Soyadı', '')
    ogr_no    = df_ogrenci.iloc[0].get('Okul No', '')
    ogr_sinif = df_ogrenci.iloc[0].get('Sınıf', '')
    ogr_okul  = df_ogrenci.iloc[0].get('Okul', '')

    html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>{ogr_ad} Raporu</title>
<style>body {{font-family:sans-serif; padding:20px; background:#f0f4f8;}} .page {{background:white; padding:30px; border-radius:12px; margin-bottom:20px; box-shadow:0 4px 10px rgba(0,0,0,0.1);}} table {{width:100%; border-collapse:collapse;}} th, td {{padding:10px; border-bottom:1px solid #ddd; text-align:left;}} </style></head><body>"""
    
    if tekil_gorev_idx is None:
        html += f"<div class='page'><h2>Genel Karne Özeti - {ogr_ad}</h2><p>{ogr_okul}</p><hr>"
        for _, row in df_islem.iterrows():
            puan  = int(pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')) if pd.notna(row.get('Toplam Puan', 0)) else 0
            html += f"<p><strong>{row.get('Ders','')} - {row.get('Gorev_Adi','')}:</strong> {puan} Puan<br>{row.get('Genel Değerlendirme Yorumu','')}</p>"
        html += "</div>"

    for _, row in df_islem.iterrows():
        toplam  = int(pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')) if pd.notna(row.get('Toplam Puan', 0)) else 0
        dinamik = json.loads(str(row.get('Dinamik_JSON', '{}'))) if pd.notna(row.get('Dinamik_JSON', '{}')) else {}
        ogrt_ad = ayarlar["kullanicilar"].get(row.get('Atanan_Ogretmen',''), {}).get("ad", "Öğretmen")
        html += f"<div class='page'><h2>{row.get('Gorev_Adi','')} ({row.get('Ders','')})</h2><h3>Toplam: {toplam}/100</h3><table><tr><th>Kriter</th><th>Puan</th><th>Açıklama</th></tr>"
        for k_id in [k.replace("_puan", "") for k in dinamik.keys() if k.endswith("_puan")]:
            baslik, maks, _ = kriter_bul(k_id, ayarlar)
            html += f"<tr><td>{baslik}</td><td>{dinamik.get(f'{k_id}_puan',0)}</td><td>{dinamik.get(f'{k_id}_aciklama','-')}</td></tr>"
        html += f"</table><p><strong>Öğretmen Yorumu:</strong> {row.get('Genel Değerlendirme Yorumu','')}</p><p style='text-align:right;'>{ogrt_ad}</p></div>"
    html += "</body></html>"
    return html

def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = "<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><style>body{font-family:sans-serif; background:#f0f4f8;} .page{background:white; margin:20px auto; padding:30px; max-width:800px; border-radius:10px; page-break-after:always;} table{width:100%; border-collapse:collapse; margin-top:15px;} th,td{padding:8px; border-bottom:1px solid #ddd; text-align:left;}</style></head><body>"
    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        dinamik = json.loads(str(b.get('Dinamik_JSON', '{}'))) if pd.notna(b.get('Dinamik_JSON', '{}')) else {}
        html += f"<div class='page'><h2>{b.get('Gorev_Adi','')} - {ogrt_brans}</h2><p><strong>Öğrenci:</strong> {b.get('Öğrenci Adı Soyadı','')} | <strong>Sınıf:</strong> {b.get('Sınıf','')} | <strong>Puan:</strong> {b.get('Toplam Puan',0)}</p><table><tr><th>Kriter</th><th>Max</th><th>Alınan</th><th>Açıklama</th></tr>"
        for k in aktif_kriterler:
            html += f"<tr><td>{k['baslik']}</td><td>{k['max']}</td><td>{dinamik.get(f'{k['id']}_puan',0)}</td><td>{dinamik.get(f'{k['id']}_aciklama','-')}</td></tr>"
        html += f"</table><p><strong>Yorum:</strong> {b.get('Genel Değerlendirme Yorumu','')}</p><p style='text-align:right;'>{ogrt_ad}</p></div>"
    html += "</body></html>"
    return html

def sinif_analiz_raporu(df_sinif, sinif_adi, ogrt_ad):
    df_p = df_sinif.dropna(subset=['Toplam Puan']).copy()
    df_p['Toplam Puan'] = pd.to_numeric(df_p['Toplam Puan'], errors='coerce').fillna(0)
    ortalama = round(df_p['Toplam Puan'].mean(), 1) if len(df_p) > 0 else 0
    html = f"<!DOCTYPE html><html lang='tr'><head><meta charset='UTF-8'><style>body{{font-family:sans-serif; background:white; padding:30px;}} table{{width:100%; border-collapse:collapse;}} th,td{{padding:10px; border:1px solid #ddd;}}</style></head><body><h1>{sinif_adi} Analiz Raporu</h1><p>Öğretmen: {ogrt_ad} | Ortalama: {ortalama}</p><table><tr><th>#</th><th>No</th><th>İsim</th><th>Görev</th><th>Puan</th></tr>"
    for i, (_, row) in enumerate(df_p.sort_values('Toplam Puan', ascending=False).iterrows(), 1):
        html += f"<tr><td>{i}</td><td>{row.get('Okul No','')}</td><td>{row.get('Öğrenci Adı Soyadı','')}</td><td>{row.get('Gorev_Adi','')}</td><td>{row.get('Toplam Puan',0)}</td></tr>"
    html += "</table></body></html>"
    return html

# ==========================================
# 10. YAPAY ZEKA BAĞLANTILARI
# ==========================================
def isme_hitap_et(tam_isim):
    """Öğrencinin sadece adını (veya adlarını) alır, soyadını atar."""
    isim_parcalari = str(tam_isim).strip().split()
    if len(isim_parcalari) > 1:
        return " ".join(isim_parcalari[:-1]) # Son kelimeyi (soyadı) at
    return tam_isim

def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    seviye = "".join(filter(str.isdigit, str(bilgi_dict.get("Sınıf", "7")))) or "7"
    ogrenci_isim = isme_hitap_et(bilgi_dict.get('Öğrenci Adı Soyadı', 'Öğrenci'))
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])
    
    prompt = f"""Sen profesyonel bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}. {seviye}. Sınıf öğrencin sevgili {ogrenci_isim}'i değerlendiriyorsun.
Lütfen öğrenciye doğrudan 'Sevgili {ogrenci_isim}, ...' şeklinde hitap ederek şefkatli, pedagojik ve motive edici konuş. (Soyadını asla kullanma).
Değerlendirme Kriterleri:\n{kriter_ozeti}\nGÖREV MODU: """

    if mod == "A": prompt += f"""YORUMDAN PUAN ÜRETME. Öğretmenin notu: "{ham_metin}"\nBu nota göre pedagojik açıklamalar yaz ve puan belirle."""
    elif mod == "B": prompt += f"""HEDEF PUANDAN YORUM ÜRETME. Hedef: {hedef_puan}/100\nBu puana ulaşacak şekilde kriterlere puan dağıt ve açıklamalar yaz."""
    else:
        ozet = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA. Öğretmen şu puanları verdi:\n{ozet}\nSadece pedagojik açıklamalar yaz. PUANLARI DEĞİŞTİRME."""

    prompt += """\nEKSTRA: "genel" anahtarında öğrenciye hitap eden ("Sevgili İsim, ...") motive edici bir genel yorum yaz.
SADECE GEÇERLİ JSON ÜRET:\n{ "puanlar": { "k1": 40 }, "aciklamalar": { "k1": "..." }, "genel": "Sevgili..." }"""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw.replace("```json", "").replace("```", "").strip())

def ai_karne_gorusu_yaz(tam_isim, sinifi, notlar_sozlugu, ekstra_gozlem, ogrt_ad):
    ogrenci_isim = isme_hitap_et(tam_isim)
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu)])
    prompt = f"""Öğretmen {ogrt_ad} olarak {sinifi} sınıfından {ogrenci_isim}'e e-okul karne görüşü yaz.
Notları: {notlar_metni}. Gözlem: {ekstra_gozlem}
Lütfen 'Sevgili {ogrenci_isim}' diye hitap ederek motive edici, 3-4 cümlelik pedagojik bir karne görüşü üret."""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ==========================================
# 11. ÖĞRENCİ SORGULAMA EKRANI (VELİ/ÖĞRENCİ)
# ==========================================
def ogrenci_sorgu_ekrani(df, ayarlar):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔍 Öğrenci Performans Sorgulama</div>", unsafe_allow_html=True)
    
    col_il, col_ilce, col_ok = st.columns(3)
    okul_listesi_duz = tum_okul_listesi_duz_getir(ayarlar["okullar"])
    s_okul_tam = st.selectbox("🏫 Okulunuzu Bulun (İl / İlçe / Okul)", ["— Seçiniz —"] + okul_listesi_duz)
    s_sinif = st.text_input("📚 Sınıf (Örn: 7/A)")
    s_no    = st.text_input("🔢 Okul Numaranız")

    if st.button("🔍 Sonuçlarımı Getir", use_container_width=True):
        if s_okul_tam == "— Seçiniz —" or not s_no.strip():
            st.warning("Lütfen okul seçip numaranızı girin.")
        else:
            filtre = (df['Okul'] == s_okul_tam) & (df['Okul No'] == s_no.strip())
            if s_sinif.strip(): filtre = filtre & (df['Sınıf'] == s_sinif.strip())
            sonuclar = df[filtre]

            if sonuclar.empty:
                st.error("❌ Kayıt bulunamadı.")
            else:
                st.success(f"👋 Hoş geldin {sonuclar.iloc[0]['Öğrenci Adı Soyadı']}! {len(sonuclar)} kayıt bulundu.")
                toplu_html = ogrenci_karnesi_html_uret(sonuclar, ayarlar)
                st.download_button("📥 Tüm Dönem Karnemi İndir", data=toplu_html, file_name="Tüm_Karne.html", mime="text/html")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 12. GİRİŞ EKRANI (İl-İlçe-Okul Dinamik Yapısı)
# ==========================================
def giris_ekrani(df, ayarlar):
    tab_ogr, tab_ogrt = st.tabs(["🎓 Öğrenci/Veli Girişi", "👨‍🏫 Öğretmen/İdare Girişi"])
    with tab_ogr:
        ogrenci_sorgu_ekrani(df, ayarlar)
    with tab_ogrt:
        c1, c2, c3 = st.columns([1, 1.8, 1])
        with c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            g1, g2, g3 = st.tabs(["🔐 Giriş", "📝 Kayıt Ol", "🔑 Şifremi Unuttum"])
            
            with g1:
                if ayarlar.get("sistem_kilitli", False): st.warning("🔒 Sistem kapalı.")
                k_adi = st.text_input("Kullanıcı Adı", key="l_kadi")
                sifre = st.text_input("Şifre", type="password", key="l_sifre")
                if st.button("Giriş Yap →", use_container_width=True):
                    user = ayarlar["kullanicilar"].get(k_adi)
                    if user and user["sifre"] == sifre:
                        if user.get("rol") != "admin" and not user.get("onayli", True):
                            st.warning("⏳ Hesabınız onay bekliyor.")
                        elif ayarlar.get("sistem_kilitli", False) and user.get("rol") != "admin":
                            st.error("🔒 Sistem kilitli.")
                        else:
                            st.session_state.update({"giris_yapti": True, "aktif_kullanici": k_adi, "kullanici_bilgi": user})
                            st.rerun()
                    else:
                        st.error("❌ Hatalı bilgi!")

           with g2:
                st.markdown("##### 📍 Kurum Bilgileri")
                st.info("💡 Lütfen önce okulunuzun listede olup olmadığını kontrol edin. Aynı okulun 2 farklı isimle kaydedilmemesi için, sadece listede YOKSA 'Yeni Okul Ekle' seçeneğini kullanın.")
                
                il_listesi = list(ayarlar["okullar"].keys())
                
                # İL SEÇİMİ
                sec_il = st.selectbox("İl Seçiniz", ["— Seçiniz —", "➕ Yeni İl Ekle"] + il_listesi)
                if sec_il == "➕ Yeni İl Ekle":
                    sec_il = st.selectbox("Türkiye İlleri", ["— Listeden Seç —"] + TUM_ILLER)
                
                # İLÇE SEÇİMİ
                sec_ilce = "— Seçiniz —"
                if sec_il and sec_il not in ["— Seçiniz —", "➕ Yeni İl Ekle", "— Listeden Seç —"]:
                    ilce_listesi = list(ayarlar["okullar"].get(sec_il, {}).keys())
                    sec_ilce = st.selectbox("İlçe Seçiniz", ["— Seçiniz —", "➕ Yeni İlçe Ekle"] + ilce_listesi)
                    if sec_ilce == "➕ Yeni İlçe Ekle":
                        sec_ilce = st.text_input("İlçe Adını Yazınız").strip().title()

                # OKUL SEÇİMİ
                sec_okul = "— Seçiniz —"
                if sec_ilce and sec_ilce not in ["— Seçiniz —", "➕ Yeni İlçe Ekle"]:
                    okul_listesi = ayarlar["okullar"].get(sec_il, {}).get(sec_ilce, [])
                    sec_okul = st.selectbox("Okulunuzu Seçiniz", ["— Seçiniz —", "➕ Yeni Okul Ekle"] + okul_listesi)
                    if sec_okul == "➕ Yeni Okul Ekle":
                        sec_okul = st.text_input("Okulun Tam Adını Yazınız (Örn: Süleyman Demirel İlkokulu)").strip().title()

                st.markdown("##### 👤 Kişisel Bilgiler")
                r_ad     = st.text_input("Ad Soyad", key="r_ad")
                r_brans  = st.text_input("Branş", key="r_brans")
                r_eposta = st.text_input("E-posta", key="r_eposta")
                r_kadi   = st.text_input("Kullanıcı Adı Seçin", key="r_kadi")
                r_sifre  = st.text_input("Şifre", type="password", key="r_sifre")

                if st.button("Kayıt Ol", use_container_width=True):
                    tam_okul_adi = f"{sec_il} / {sec_ilce} / {sec_okul}"
                    
                    if r_kadi in ayarlar["kullanicilar"]:
                        st.error("Bu kullanıcı adı alınmış.")
                    elif not (r_kadi and r_sifre and r_ad and sec_il and sec_ilce and sec_okul and "Seçiniz" not in tam_okul_adi):
                        st.warning("Lütfen il, ilçe, okul ve tüm kişisel alanları eksiksiz doldurun.")
                    else:
                        if sec_il not in ayarlar["okullar"]: ayarlar["okullar"][sec_il] = {}
                        if sec_ilce not in ayarlar["okullar"][sec_il]: ayarlar["okullar"][sec_il][sec_ilce] = []
                        if sec_okul not in ayarlar["okullar"][sec_il][sec_ilce]: 
                            ayarlar["okullar"][sec_il][sec_ilce].append(sec_okul)

                        is_auto = ayarlar.get("otomatik_onay", True)
                        ayarlar["kullanicilar"][r_kadi] = {
                            "sifre": r_sifre, "rol": "ogretmen", "ad": r_ad,
                            "okul": tam_okul_adi, "brans": r_brans, "eposta": r_eposta, "onayli": is_auto
                        }
                        ayar_kaydet(ayarlar)
                        st.success("✅ Kayıt başarılı!")
                        time.sleep(1)
                        st.rerun()

            with g3:
                u_eposta = st.text_input("Kayıtlı E-posta")
                if st.button("🔑 Şifre Gönder"):
                    for k, u in ayarlar["kullanicilar"].items():
                        if u.get("eposta") == u_eposta:
                            y_sifre = sifre_olustur()
                            ok, _ = eposta_gonder(u_eposta, "Şifreniz", f"Yeni şifre: {y_sifre}")
                            if ok:
                                ayarlar["kullanicilar"][k]["sifre"] = y_sifre
                                ayar_kaydet(ayarlar)
                                st.success("Gönderildi.")
                            break
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 13. KULLANIM KILAVUZU
# ==========================================
def kullanim_kilavuzu():
    with st.expander("📖 PROPERKAR360 Kullanım Kılavuzu"):
        st.markdown("Sistem Türkiye geneli çalışmaktadır. İl/İlçe seçerek okulunuzu bulabilir veya listeye ekleyebilirsiniz.")

# ==========================================
# 14. ŞABLON YÖNETİM MODÜLÜ
# ==========================================
def sablon_yonetimi_ui(ayarlar, kb, rol):
    st.markdown("#### 📐 Ölçek (Şablon) Yönetimi")
    t_man, t_ex = st.tabs(["✍️ Manuel Oluştur", "📥 Excel ile Yükle"])
    with t_man:
        if "t_df" not in st.session_state: st.session_state["t_df"] = pd.DataFrame([{"Başlık": "İçerik", "Puan": 50, "Açıklama": ""}])
        s_isim_yeni = st.text_input("Şablon Adı", key=f"man_sablon_ad_{rol}")
        e_df = st.data_editor(st.session_state["t_df"], num_rows="dynamic", use_container_width=True)
        if st.button("💾 Kaydet", key=f"btn_man_kaydet_{rol}"):
            if pd.to_numeric(e_df["Puan"], errors="coerce").sum() == 100 and s_isim_yeni:
                tam_isim = s_isim_yeni if rol == "admin" else f"{s_isim_yeni} (Ekleyen: {kb['ad']})"
                ayarlar["sablonlar"][tam_isim] = [{"id": f"k{i+1}", "baslik": str(r["Başlık"]), "max": int(r["Puan"]), "icon": "📌", "aciklama": str(r.get("Açıklama",""))} for i, r in e_df.iterrows()]
                ayar_kaydet(ayarlar)
                st.success("Eklendi!"); st.rerun()
            else: st.error("Toplam puan 100 olmalı!")

# ==========================================
# 15. YÖNETİM PANELİ (Tüm İşlemler)
# ==========================================
def yonetim_paneli(df, ayarlar):
    _init_nav()
    aktif_id = st.session_state["aktif_kullanici"]
    kb       = st.session_state["kullanici_bilgi"]
    rol      = kb["rol"]
    admin_bakis = st.session_state.get("admin_bakis_modu", False)
    admin_bakis_ogrt = st.session_state.get("admin_bakis_ogretmen", None)

    col_profil1, col_profil2 = st.columns([4, 1])
    with col_profil1:
        st.markdown(f"<div class='profil-bar'><div><div style='font-size:1.15rem;font-weight:900;'>{'👁️ ' if admin_bakis else '👋 '}{kb['ad']}</div><div style='font-size:0.88rem;color:#64748b;'>{kb.get('okul','Yönetici')} | {kb.get('brans','')}</div></div></div>", unsafe_allow_html=True)
    with col_profil2:
        if admin_bakis:
            if st.button("← Admin'e Dön", use_container_width=True): st.session_state.update({"admin_bakis_modu":False,"admin_bakis_ogretmen":None}); st.rerun()
        else:
            if st.button("🚪 Çıkış Yap", use_container_width=True): st.session_state.clear(); st.rerun()

    df_yetkili = df if rol == "admin" and not admin_bakis else df[(df['Okul'] == kb.get("okul")) & ((df['Atanan_Ogretmen'] == aktif_id) | (df['Atanan_Ogretmen'] == 'admin'))]
    kullanim_kilavuzu()
    render_ana_nav(rol, admin_bakis)
    aktif_ana = st.session_state.get("nav_ana", "ogr_gorev")

    # --- ÖĞRENCİ GÖREV ---
    if aktif_ana == "ogr_gorev":
        render_nav_bar(ALT_MENU_OGR_GOREV, "nav_ogr_alt", is_main=False)
        aktif_ogr = st.session_state.get("nav_ogr_alt", "excel_yukle")

        if aktif_ogr == "excel_yukle":
            st.markdown('<div class="glass-card"><div class="section-header">📥 Excel ile Görev Tanımla</div>', unsafe_allow_html=True)
            h_okul = kb.get("okul") if rol != "admin" else st.selectbox("Okul", tum_okul_listesi_duz_getir(ayarlar["okullar"]))
            g_tur  = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans"])
            g_isim = st.text_input("Görevin Adı")
            uploaded_file = st.file_uploader("Excel Yükle", type=['xlsx'])
            if st.button("🚀 Ata", use_container_width=True) and uploaded_file and g_isim:
                excel_df = pd.read_excel(uploaded_file, dtype={"Okul No": str})
                db_records = []
                for _, row in excel_df.dropna(subset=[excel_df.columns[0]]).iterrows():
                    o_no = str(row[excel_df.columns[0]]).strip().replace('.0','')
                    if df[(df['Okul']==h_okul)&(df['Okul No']==o_no)&(df['Gorev_Adi']==g_isim)].empty:
                        db_records.append({'okul': h_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': aktif_id, 'ders': kb.get("brans","Genel"), 'okul_no': o_no, 'ogrenci_adi_soyadi': row[excel_df.columns[1]], 'sinif': str(row[excel_df.columns[2]]), 'gorev_turu': g_tur, 'gorev_adi': g_isim, 'dinamik_json': {}})
                if db_records:
                    supabase.table('gorevler').insert(db_records).execute(); st.cache_data.clear(); st.success("Eklendi!"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif aktif_ogr == "tekil_ekle":
            st.markdown('<div class="glass-card"><div class="section-header">➕ Tekil Ekle</div>', unsafe_allow_html=True)
            with st.form("tekil_ekle_form"):
                m_no, m_ad, m_sinif = st.text_input("Okul No"), st.text_input("Ad Soyad"), st.text_input("Sınıf")
                m_gtur, m_gadi = st.selectbox("Tür", ["Proje", "Performans"]), st.text_input("Görev Adı")
                if st.form_submit_button("Ekle") and m_no and m_ad and m_gadi:
                    supabase.table('gorevler').insert({'okul': kb.get("okul"), 'ekleyen': aktif_id, 'atanan_ogretmen': aktif_id, 'ders': kb.get("brans",""), 'okul_no': m_no.strip(), 'ogrenci_adi_soyadi': m_ad, 'sinif': m_sinif, 'gorev_turu': m_gtur, 'gorev_adi': m_gadi, 'dinamik_json': {}}).execute()
                    st.cache_data.clear(); st.success("Eklendi!"); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif aktif_ogr == "silme":
            render_nav_bar(ALT_MENU_SIL, "nav_sil_alt", is_main=False)
            aktif_sil = st.session_state.get("nav_sil_alt", "tekil_sil")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if aktif_sil == "tekil_sil":
                silinecek = st.selectbox("Kayıt Seç", ["— Seçiniz —"] + df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Gorev_Adi']}", axis=1).tolist() if not df_yetkili.empty else [])
                if st.button("Sil") and silinecek != "— Seçiniz —":
                    supabase.table('gorevler').delete().eq('okul_no', silinecek.split(" - ")[0]).eq('gorev_adi', silinecek.split(" - ")[1]).execute()
                    st.cache_data.clear(); st.rerun()
            elif aktif_sil == "sinif_sil":
                sil_okul2 = kb.get("okul") if rol != "admin" else st.selectbox("Okul", tum_okul_listesi_duz_getir(ayarlar["okullar"]))
                sec_sinif = st.multiselect("Sınıflar", sorted(df[df['Okul'] == sil_okul2]['Sınıf'].dropna().unique()))
                if sec_sinif and st.button("Sınıfı Sil"):
                    supabase.table('gorevler').delete().eq('okul', sil_okul2).in_('sinif', sec_sinif).execute()
                    st.cache_data.clear(); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- AI DEĞERLENDİRME ---
    elif aktif_ana == "ai_degerlendirme":
        st.markdown('<div class="glass-card"><div class="section-header">🤖 Yapay Zeka (İsme Özel Hitap)</div>', unsafe_allow_html=True)
        if not df_yetkili.empty:
            c1, c2 = st.columns([2, 1])
            sec_gor = c1.selectbox("🎯 Öğrenci", ["— Seçiniz —"] + df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist())
            aktif_sablon = ayarlar["sablonlar"].get(c2.selectbox("📋 Şablon", list(ayarlar.get("sablonlar", {}).keys())), CEKIRDEK_SABLON)
            if sec_gor != "— Seçiniz —":
                o_no, g_ad = sec_gor.split(" - ")[0].strip(), sec_gor.split(" | ")[1].strip()
                bilgi = df[(df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_ad)].iloc[0]
                
                ai_modu = st.radio("Mod", ["A", "B"], format_func=lambda x: "📝 Yorum Gir, AI Puanlasın" if x=="A" else "🎯 Hedef Puan Ver, AI Dağıtsın", horizontal=True)
                ham_metin, hedef_puan = "", 85
                if ai_modu == "A": ham_metin = st.text_area("Öğretmen notunuz:")
                else: hedef_puan = st.slider("Hedef Puan", 0, 100, 85)

                if st.button("✨ Yapay Zekayı Çalıştır"):
                    with st.spinner("İsme özel analiz ediliyor..."):
                        res = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, {}, kb.get("ad",""), bilgi['Ders'])
                        for k in aktif_sablon:
                            st.session_state[f"vp_{k['id']}"] = int(res.get("puanlar", {}).get(k['id'], 0))
                            st.session_state[f"va_{k['id']}"] = res.get("aciklamalar", {}).get(k['id'], "")
                        st.session_state["vg"] = res.get("genel", "")
                        st.success("✅ Hazır!")

                with st.form("kayit"):
                    top = 0
                    for k in aktif_sablon:
                        st.markdown(f"**{k['baslik']}** (Max: {k['max']})")
                        c_a, c_b = st.columns([1,3])
                        pv = c_a.number_input("P", 0, k['max'], key=f"vp_{k['id']}", label_visibility="collapsed")
                        st.session_state[f"va_{k['id']}"] = c_b.text_area("A", key=f"va_{k['id']}", height=68, label_visibility="collapsed")
                        top += pv
                    gv = st.text_area("💬 Genel Yorum", key="vg")
                    if st.form_submit_button(f"💾 Kaydet (Toplam: {top})"):
                        d_k = {f"{k['id']}_{t}": st.session_state[f"v{t[0]}_{k['id']}"] for k in aktif_sablon for t in ["puan","aciklama"]}
                        supabase.table('gorevler').update({'dinamik_json': d_k, 'genel_degerlendirme_yorumu': gv, 'toplam_puan': top}).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                        st.cache_data.clear(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RAPORLAR VE EOKUL ---
    elif aktif_ana == "raporlar":
        render_nav_bar(ALT_MENU_RAPORLAR, "nav_rapor_alt", is_main=False)
        aktif_rap = st.session_state.get("nav_rapor_alt", "sinif_rapor")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if aktif_rap == "sinif_rapor" and not df_yetkili.empty:
            r_sinif = st.selectbox("Sınıf", ["Tümü"] + sorted(df_yetkili['Sınıf'].dropna().unique()))
            df_r = df_yetkili if r_sinif == "Tümü" else df_yetkili[df_yetkili['Sınıf'] == r_sinif]
            st.dataframe(df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Adi','Toplam Puan']], use_container_width=True)
            if st.button("🖨️ HTML Karne"):
                st.download_button("İndir", data=toplu_karne_html_dosyasi_uret(df_r, kb.get("ad",""), kb.get("brans",""), CEKIRDEK_SABLON), file_name="Karne.html", mime="text/html")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- AYARLAR VE ADMIN (OKUL YÖNETİMİ) ---
    elif aktif_ana == "ayarlar":
        render_nav_bar(ALT_MENU_AYARLAR_ADMIN if rol == "admin" else ALT_MENU_AYARLAR_OGRT, "nav_ayar_alt", is_main=False)
        aktif_ayar = st.session_state.get("nav_ayar_alt", "profil")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        if aktif_ayar == "okullar" and rol == "admin":
            st.markdown("### 🏢 Türkiye Geneli İl / İlçe / Okul Hiyerarşisi Yönetimi")
            
            c_il, c_ilce, c_ok = st.columns(3)
            # İL SEÇİMİ
            mevcut_iller = list(ayarlar["okullar"].keys())
            secili_il_admin = c_il.selectbox("İl Seç", ["— Seçiniz —", "➕ İl Ekle"] + mevcut_iller)
            if secili_il_admin == "➕ İl Ekle":
                yeni_il = c_il.selectbox("Türkiye İlleri", ["— Listeden Seç —"] + TUM_ILLER)
                if c_il.button("İli Ekle") and yeni_il != "— Listeden Seç —":
                    ayarlar["okullar"][yeni_il] = {}
                    ayar_kaydet(ayarlar); st.rerun()
            
            # İLÇE SEÇİMİ
            if secili_il_admin and secili_il_admin not in ["— Seçiniz —", "➕ İl Ekle"]:
                mevcut_ilceler = list(ayarlar["okullar"][secili_il_admin].keys())
                secili_ilce_admin = c_ilce.selectbox("İlçe Seç", ["— Seçiniz —", "➕ İlçe Ekle"] + mevcut_ilceler)
                if secili_ilce_admin == "➕ İlçe Ekle":
                    yeni_ilce = c_ilce.text_input("Yeni İlçe Adı")
                    if c_ilce.button("İlçeyi Ekle") and yeni_ilce:
                        ayarlar["okullar"][secili_il_admin][yeni_ilce.strip().title()] = []
                        ayar_kaydet(ayarlar); st.rerun()
                        
                # OKUL SEÇİMİ
                if secili_ilce_admin and secili_ilce_admin not in ["— Seçiniz —", "➕ İlçe Ekle"]:
                    mevcut_okullar_admin = ayarlar["okullar"][secili_il_admin][secili_ilce_admin]
                    secili_okul_admin = c_ok.selectbox("Okul Seç (Silmek İçin)", ["— Seçiniz —", "➕ Okul Ekle"] + mevcut_okullar_admin)
                    if secili_okul_admin == "➕ Okul Ekle":
                        yeni_okul = c_ok.text_input("Yeni Okul Adı")
                        if c_ok.button("Okulu Ekle") and yeni_okul:
                            ayarlar["okullar"][secili_il_admin][secili_ilce_admin].append(yeni_okul.strip().title())
                            ayar_kaydet(ayarlar); st.rerun()
                    elif secili_okul_admin != "— Seçiniz —":
                        if c_ok.button("🗑️ Okulu Sil"):
                            ayarlar["okullar"][secili_il_admin][secili_ilce_admin].remove(secili_okul_admin)
                            ayar_kaydet(ayarlar); st.rerun()

        elif aktif_ayar == "okullar" and rol == "admin":
            st.markdown("### 🏢 Türkiye Geneli İl / İlçe / Okul Hiyerarşisi Yönetimi")
            
            tab_ekle, tab_birlestir = st.tabs(["➕ Ekle / Sil", "🔗 Mükerrer Okulları Birleştir"])

            with tab_ekle:
                c_il, c_ilce, c_ok = st.columns(3)
                mevcut_iller = list(ayarlar["okullar"].keys())
                secili_il_admin = c_il.selectbox("İl Seç", ["— Seçiniz —", "➕ İl Ekle"] + mevcut_iller)
                if secili_il_admin == "➕ İl Ekle":
                    yeni_il = c_il.selectbox("Türkiye İlleri", ["— Listeden Seç —"] + TUM_ILLER)
                    if c_il.button("İli Ekle") and yeni_il != "— Listeden Seç —":
                        ayarlar["okullar"][yeni_il] = {}
                        ayar_kaydet(ayarlar); st.rerun()
                
                if secili_il_admin and secili_il_admin not in ["— Seçiniz —", "➕ İl Ekle"]:
                    mevcut_ilceler = list(ayarlar["okullar"][secili_il_admin].keys())
                    secili_ilce_admin = c_ilce.selectbox("İlçe Seç", ["— Seçiniz —", "➕ İlçe Ekle"] + mevcut_ilceler)
                    if secili_ilce_admin == "➕ İlçe Ekle":
                        yeni_ilce = c_ilce.text_input("Yeni İlçe Adı")
                        if c_ilce.button("İlçeyi Ekle") and yeni_ilce:
                            ayarlar["okullar"][secili_il_admin][yeni_ilce.strip().title()] = []
                            ayar_kaydet(ayarlar); st.rerun()
                            
                    if secili_ilce_admin and secili_ilce_admin not in ["— Seçiniz —", "➕ İlçe Ekle"]:
                        mevcut_okullar_admin = ayarlar["okullar"][secili_il_admin][secili_ilce_admin]
                        secili_okul_admin = c_ok.selectbox("Okul Seç (Silmek İçin)", ["— Seçiniz —", "➕ Okul Ekle"] + mevcut_okullar_admin)
                        if secili_okul_admin == "➕ Okul Ekle":
                            yeni_okul = c_ok.text_input("Yeni Okul Adı")
                            if c_ok.button("Okulu Ekle") and yeni_okul:
                                ayarlar["okullar"][secili_il_admin][secili_ilce_admin].append(yeni_okul.strip().title())
                                ayar_kaydet(ayarlar); st.rerun()
                        elif secili_okul_admin != "— Seçiniz —":
                            if c_ok.button("🗑️ Okulu Sil"):
                                ayarlar["okullar"][secili_il_admin][secili_ilce_admin].remove(secili_okul_admin)
                                ayar_kaydet(ayarlar); st.rerun()

            with tab_birlestir:
                st.markdown("#### 🔗 Hatalı veya Farklı Yazılan Okulları Birleştir")
                st.markdown('<div class="info-banner">Örn: "Süleyman Akademi" ve "Süleyman Academy" olarak iki defa açılmış okulları tek isimde birleştirir. Hatalı okuldaki tüm öğretmen ve öğrenciler otomatik olarak doğru okula aktarılır.</div>', unsafe_allow_html=True)
                
                okul_listesi_duz = tum_okul_listesi_duz_getir(ayarlar["okullar"])
                col_b1, col_b2 = st.columns(2)
                
                hatali_okul = col_b1.selectbox("Silinecek (Hatalı) Okul", ["— Seçiniz —"] + okul_listesi_duz)
                hedef_okul  = col_b2.selectbox("Aktarılacak (Doğru) Okul", ["— Seçiniz —"] + okul_listesi_duz)

                if st.button("🔗 Okulları Birleştir ve Verileri Aktar", type="primary", use_container_width=True):
                    if hatali_okul == "— Seçiniz —" or hedef_okul == "— Seçiniz —" or hatali_okul == hedef_okul:
                        st.error("Lütfen iki farklı okul seçin.")
                    else:
                        # 1. Veritabanındaki Görevleri/Öğrencileri Güncelle
                        supabase.table('gorevler').update({'okul': hedef_okul}).eq('okul', hatali_okul).execute()
                        
                        # 2. Öğretmenlerin Kayıtlı Olduğu Okulu Güncelle
                        for k, u in ayarlar["kullanicilar"].items():
                            if u.get("okul") == hatali_okul:
                                ayarlar["kullanicilar"][k]["okul"] = hedef_okul
                        
                        # 3. Hatalı Okulu JSON Listesinden Sil
                        h_il, h_ilce, h_ok = [x.strip() for x in hatali_okul.split(" / ")]
                        if h_il in ayarlar["okullar"] and h_ilce in ayarlar["okullar"][h_il]:
                            if h_ok in ayarlar["okullar"][h_il][h_ilce]:
                                ayarlar["okullar"][h_il][h_ilce].remove(h_ok)
                            
                        ayar_kaydet(ayarlar)
                        st.success(f"✅ '{h_ok}' isimli hatalı okul silindi! İçindeki tüm veriler '{hedef_okul.split('/')[-1].strip()}' okuluna aktarıldı.")
                        time.sleep(2)
                        st.rerun()

# ==========================================
# 16. ANA ÇALIŞTIRMA VE FOOTER
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df = veri_yukle()
    st.markdown("<div class='hero-header'><div class='hero-title'>🧭 PROPERKAR360</div><div class='hero-subtitle'>Türkiye Geneli Proje ve Performans Değerlendirme</div></div>", unsafe_allow_html=True)
    
    if not st.session_state.get("giris_yapti", False): giris_ekrani(df, ayarlar)
    else: yonetim_paneli(df, ayarlar)

    st.markdown("<div class='app-footer'>Sistem Tasarımcısı: <strong>Sıraç AKSAN</strong> | saracaksan@gmail.com</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
