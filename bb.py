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
import random

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

def get_gemini_api_url(kullanici_anahtari=None):
    """Kullanıcının kendi anahtarı varsa onu, yoksa havuzdan rastgele birini seçer."""
    secilen_key = ""
    if kullanici_anahtari and kullanici_anahtari.strip().startswith("AIzaSy"):
        secilen_key = kullanici_anahtari.strip()
    else:
        try:
            havuz = st.secrets["GEMINI_API_KEYS"]
            secilen_key = random.choice(havuz)
        except Exception:
            # Geriye dönük uyumluluk için (Eğer eski tekli anahtar kaldıysa)
            secilen_key = st.secrets.get("GEMINI_API_KEY", "").strip()
            
    if not secilen_key:
        return None
        
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={secilen_key}"

# ==========================================
# 3. GLOBAL CSS VE RENK HİYERARŞİSİ
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ── Temel ── */
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
.hero-header::before {
    content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle at 70% 50%, rgba(255,255,255,0.06) 0%, transparent 60%);
}
.hero-title {
    font-family: 'Nunito', sans-serif; font-size: clamp(1.4rem, 4vw, 2.2rem); font-weight: 900; color: #ffffff; margin: 0; letter-spacing: -0.5px;
}
.hero-subtitle { font-size: clamp(0.85rem, 2.5vw, 1rem); color: #bfdbfe; margin-top: 5px; font-weight: 600; }
.hero-badge { display: inline-block; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); color: white; padding: 3px 14px; border-radius: 20px; font-size: 0.75rem; margin-top: 8px; font-weight: 700; }

/* ── MENÜ RENK HİYERARŞİSİ (Mavi -> Yeşil -> Kırmızı) ── */
/* Ana Menü: Pasif (Mavi), Aktif (Yeşil) */
div[data-testid="stHorizontalBlock"] .ana-menu-btn > button {
    background: #2563eb !important; 
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}
div[data-testid="stHorizontalBlock"] .ana-menu-btn.active-btn > button {
    background: #10b981 !important; /* Aktif Ana Menü Yeşil */
    box-shadow: 0 4px 15px rgba(16,185,129,0.4) !important;
}

/* Alt Menü: Pasif (Yeşil), Aktif (Kırmızı) */
div[data-testid="stHorizontalBlock"] .alt-menu-btn > button {
    background: #10b981 !important; /* Pasif Alt Menü Yeşil */
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}
div[data-testid="stHorizontalBlock"] .alt-menu-btn.active-btn > button {
    background: #ef4444 !important; /* Aktif Alt Menü Kırmızı */
    box-shadow: 0 4px 15px rgba(239,68,68,0.4) !important;
}

/* Hover Efektleri */
div[data-testid="stHorizontalBlock"] button:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.1);
}

/* ── Kart & Paneller ── */
.glass-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin-bottom: 18px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); transition: box-shadow 0.2s; }
.glass-card:hover { box-shadow: 0 4px 24px rgba(0,0,0,0.1); }
.stat-card { background: white; border-radius: 12px; padding: 16px 20px; border-left: 5px solid #2563eb; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 12px; }
.stat-card.green  { border-left-color: #10b981; }
.stat-card.orange { border-left-color: #f59e0b; }
.stat-card.red    { border-left-color: #ef4444; }
.stat-number { font-size: 2rem; font-weight: 900; color: #0f172a; line-height: 1; }
.stat-label  { font-size: 0.8rem; color: #64748b; font-weight: 600; margin-top: 4px; }
.section-header { color: #1e40af; font-weight: 800; font-size: 1.1rem; margin-bottom: 16px; border-bottom: 2px solid #bfdbfe; padding-bottom: 8px; display: flex; align-items: center; gap: 8px; }

/* ── Streamlit Native Tabs (sadece giriş ekranı için) ── */
[data-testid="stTabs"] > div[data-baseweb="tab-list"] { background: #1e293b; border-radius: 12px; padding: 7px; gap: 5px; }
[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button { background: transparent !important; color: #94a3b8 !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 0.88rem !important; padding: 8px 16px !important; }
[data-testid="stTabs"] > div[data-baseweb="tab-list"] > button[aria-selected="true"] { background: #3b82f6 !important; color: #ffffff !important; box-shadow: 0 2px 10px rgba(59,130,246,0.4) !important; }

/* ── Bildirim Banner'lar ── */
.info-banner { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #1e40af; font-weight: 600; font-size: 0.9rem; }
.warn-banner { background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #92400e; font-weight: 600; font-size: 0.9rem; }
.success-banner { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #166534; font-weight: 600; font-size: 0.9rem; }

/* ── Kriter Kartı ── */
.kriter-card { background: #f0f9ff; padding: 12px 16px; border-radius: 9px; border-left: 4px solid #2563eb; margin-bottom: 10px; }
.kriter-card .baslik { color: #1e3a8a; font-weight: 700; font-size: 0.95rem; }
.kriter-card .aciklama { color: #94a3b8; font-size: 0.82rem; margin-top: 2px; }

/* ── Footer ── */
.app-footer { background: #0f172a; color: #94a3b8; border-radius: 12px; padding: 22px 30px; margin-top: 32px; text-align: center; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER VE TÜRKİYE İLLERİ
# ==========================================
TUM_ILLER = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir", 
    "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", 
    "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", 
    "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", 
    "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir", 
    "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", 
    "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", 
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
]

DARGEÇIT_OKULLARI = [
    "60. Yıl Sarıgazi Ortaokulu", "Alayurt İlkokulu", "Alayurt Ortaokulu", "Altınoluk İlkokulu", "Altıyol İlkokulu",
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

# ── Ana menü sekmeleri ──
ANA_MENU = {
    "ogr_gorev": {"label": "👥 Öğrenci & Görev", "icon": "👥"},
    "ai_degerlendirme": {"label": "🤖 AI Değerlendirme", "icon": "🤖"},
    "raporlar": {"label": "📊 Raporlar", "icon": "📊"},
    "eokul": {"label": "📝 E-Okul Karne", "icon": "📝"},
    "ogretmen_yonetim": {"label": "👨‍🏫 Öğretmen Yönetimi", "icon": "👨‍🏫"},
    "ayarlar": {"label": "⚙️ Ayarlar & Profil", "icon": "⚙️"},
}

ALT_MENU_OGR_GOREV = [
    ("excel_yukle",   "📥 Excel ile Yükle"),
    ("tekil_ekle",    "➕ Tekil Ekle"),
    ("havuz_ata",     "🏫 Havuzdan Görev Ata"),
    ("gecmis_duzenle","✏️ Geçmişi Düzenle"),
    ("silme",         "🗑️ Silme İşlemleri"),
]
ALT_MENU_RAPORLAR = [
    ("sinif_rapor",   "📊 Sınıf Raporları"),
    ("yedekleme",     "💾 Veri Yedekleme"),
]
ALT_MENU_AYARLAR_ADMIN = [
    ("sistem",        "🔒 Sistem Kontrolü"),
    ("okullar",       "🏢 İl/İlçe/Okul Yönetimi"),
    ("sablonlar",     "📐 Ölçek / Şablon"),
]
ALT_MENU_AYARLAR_OGRT = [
    ("profil",        "👤 Profilim"),
    ("sablonlar",     "📐 Ölçek / Şablon"),
]
ALT_MENU_SIL = [
    ("tekil_sil",     "📌 Tekil Kayıt Sil"),
    ("sinif_sil",     "🏫 Sınıf Toplu Sil"),
    ("okul_sil",      "🏢 Okul Toplu Sil"),
]

# ==========================================
# 5. ÖZEL NAVİGASYON YARDIMCILARI (RENKLİ VE MOBİL UYUMLU)
# ==========================================
def _init_nav():
    if "nav_ana" not in st.session_state: st.session_state["nav_ana"] = "ogr_gorev"
    if "nav_ogr_alt" not in st.session_state: st.session_state["nav_ogr_alt"] = "excel_yukle"
    if "nav_rapor_alt" not in st.session_state: st.session_state["nav_rapor_alt"] = "sinif_rapor"
    if "nav_ayar_alt" not in st.session_state: st.session_state["nav_ayar_alt"] = "profil"
    if "nav_sil_alt" not in st.session_state: st.session_state["nav_sil_alt"] = "tekil_sil"

def render_nav_bar(menu_items: list, state_key: str, is_main=False):
    # Mobilde butonların düzgün yayılması için sütun yapısı
    cols = st.columns(len(menu_items))
    aktif = st.session_state.get(state_key, menu_items[0][0])
    
    # CSS için tetikleyici sınıflar
    menu_class = "ana-menu-btn" if is_main else "alt-menu-btn"
    
    for col, (key, label) in zip(cols, menu_items):
        is_active = aktif == key
        display_label = f"◉ {label}" if is_active else label
        active_class = "active-btn" if is_active else "inactive-btn"
        
        # 'with col:' kullanarak butonları Streamlit konteynerinde hapsediyoruz (Mobil taşmaları engeller)
        with col:
            st.markdown(f'<div class="{menu_class} {active_class}">', unsafe_allow_html=True)
            if st.button(display_label, key=f"navbtn_{state_key}_{key}", use_container_width=True):
                st.session_state[state_key] = key
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def render_ana_nav(rol: str, admin_bakis: bool):
    items = [
        ("ogr_gorev",         "👥 Öğrenci & Görev"),
        ("ai_degerlendirme",  "🤖 AI Değerlendirme"),
        ("raporlar",          "📊 Raporlar"),
        ("eokul",             "📝 E-Okul Karne"),
    ]
    if rol == "admin" and not admin_bakis:
        items.append(("ogretmen_yonetim", "👨‍🏫 Öğretmen Yönetimi"))
    items.append(("ayarlar", "⚙️ Ayarlar & Profil"))
    
    st.markdown('<div style="margin-bottom:15px;">', unsafe_allow_html=True)
    render_nav_bar(items, "nav_ana", is_main=True)
    st.markdown('</div>', unsafe_allow_html=True)
# ==========================================
# 6. VERİTABANI YÖNETİMİ
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
                    "admin": {"sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi", "brans": "Tüm Dersler", "okul": "", "eposta": "saracaksan@gmail.com", "onayli": True}
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
        <div style="background:white;border-radius:12px;padding:30px;max-width:500px;
             margin:0 auto;border-top:5px solid #2563eb;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
            <h2 style="color:#1e3a8a;margin-top:0;">🧭 PUSULA 360</h2>
            <p style="color:#334155;line-height:1.6;">{icerik}</p>
            <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">
            <p style="color:#94a3b8;font-size:0.85rem;">Bu e-posta otomatik gönderilmiştir.</p>
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
            if kr["id"] == k_id:
                return kr["baslik"], kr["max"], kr.get("icon", "📌")
    for kr in CEKIRDEK_SABLON:
        if kr["id"] == k_id:
            return kr["baslik"], kr["max"], kr.get("icon", "📌")
    return "Kriter", 100, "📌"

def isme_hitap_et(tam_isim):
    isim_parcalari = str(tam_isim).strip().split()
    if len(isim_parcalari) > 1:
        return " ".join(isim_parcalari[:-1])
    return tam_isim

# ==========================================
# 9. HTML RAPOR ŞABLONLARİ (PROFESYONEL ÇIKTILAR)
# ==========================================
def ogrenci_karnesi_html_uret(df_ogrenci, ayarlar, tekil_gorev_idx=None):
    if tekil_gorev_idx is not None:
        df_islem = df_ogrenci.loc[[tekil_gorev_idx]]
    else:
        df_islem = df_ogrenci

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

    if tekil_gorev_idx is None:
        html += f"""
        <div class="page" style="border-top:6px solid #10b981;">
            <div class="header">
                <h1>Dönem Sonu Performans & Karne Özeti</h1>
                <p>{ogr_okul}</p>
            </div>
            <div class="ogrenci-bilgi">
                <div class="bilgi-kutu"><div class="bilgi-etiket">Öğrenci Adı</div><div class="bilgi-deger">{ogr_ad}</div></div>
                <div class="bilgi-kutu"><div class="bilgi-etiket">Okul No</div><div class="bilgi-deger">{ogr_no}</div></div>
                <div class="bilgi-kutu"><div class="bilgi-etiket">Sınıf</div><div class="bilgi-deger">{ogr_sinif}</div></div>
                <div class="bilgi-kutu"><div class="bilgi-etiket">Toplam Görev</div><div class="bilgi-deger">{len(df_islem)}</div></div>
            </div>
            <h3 style="color:#1e40af;">📌 Tüm Öğretmenlerin Genel Karne Görüşleri</h3>"""
        for _, row in df_islem.iterrows():
            ders  = row.get('Ders', 'Ders')
            g_adi = row.get('Gorev_Adi', '')
            puan  = int(pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')) if pd.notna(row.get('Toplam Puan', 0)) else 0
            yorum = row.get('Genel Değerlendirme Yorumu', '')
            if yorum:
                html += f"""
                <div style="margin-bottom:15px; border-bottom:1px dashed #cbd5e1; padding-bottom:10px;">
                    <strong style="color:#0f172a;">{ders} - {g_adi} (Puan: {puan}):</strong><br>
                    <span style="color:#475569;">{yorum}</span>
                </div>"""
        html += "</div>"

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
                  <th style="width:20%">Kriter</th>
                  <th style="text-align:center;width:10%">Puan</th>
                  <th style="width:70%">Öğretmen Açıklaması</th>
                </tr>"""

        kriter_idler = [k.replace("_puan", "") for k in dinamik.keys() if k.endswith("_puan")]
        for k_id in kriter_idler:
            baslik, maks, icon = kriter_bul(k_id, ayarlar)
            p_val = dinamik.get(f"{k_id}_puan", 0)
            a_val = dinamik.get(f"{k_id}_aciklama", "-")
            html += f"""
            <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                <td style="padding: 15px; border-right: 1px solid #e2e8f0;">
                    <div style="font-size: 1.1rem; color: #1e3a8a;"><strong>{icon} {baslik}</strong></div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 4px;">Maksimum: {maks} Puan</div>
                </td>
                <td style="text-align: center; vertical-align: middle; padding: 15px; border-right: 1px solid #e2e8f0;">
                    <div style="background-color: #dbeafe; color: #1d4ed8; padding: 10px; border-radius: 8px; font-size: 1.3rem; font-weight: 900; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: inline-block; min-width: 40px;">{p_val}</div>
                </td>
                <td style="padding: 15px; color: #334155; line-height: 1.6; font-size: 0.95rem;">
                    {a_val}
                </td>
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
    html = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Öğrenci Performans Karnesi</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
  body { font-family: 'Plus Jakarta Sans', Arial, sans-serif; background: #e2e8f0; margin: 0; padding: 20px; }
  .page { 
      background: #ffffff; width: 100%; max-width: 800px; margin: 0 auto 30px auto; padding: 40px; 
      border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
      page-break-after: always; position: relative; overflow: hidden;
  }
  .page::before {
      content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 8px;
      background: linear-gradient(90deg, #1e3a8a, #3b82f6, #10b981);
  }
  .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; margin-bottom: 25px; }
  .kurum-bilgi { font-size: 0.9rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
  .baslik-ana { font-size: 1.6rem; color: #0f172a; font-weight: 800; margin: 0; }
  .baslik-alt { font-size: 1.1rem; color: #3b82f6; font-weight: 600; margin-top: 5px; }
  .puan-rozet { 
      background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 16px; 
      padding: 15px 25px; text-align: center; min-width: 100px;
  }
  .puan-deger { font-size: 2.5rem; font-weight: 900; color: #1e3a8a; line-height: 1; }
  .puan-metin { font-size: 0.8rem; font-weight: 700; color: #64748b; margin-top: 5px; text-transform: uppercase; }
  
  .ogrenci-karti { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }
  .bilgi-öğe { flex: 1; min-width: 150px; }
  .bilgi-etiket { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
  .bilgi-deger { font-size: 1.1rem; color: #0f172a; font-weight: 700; border-bottom: 1px dashed #cbd5e1; padding-bottom: 4px; }
  
  table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
  th { background: #1e293b; color: #ffffff; padding: 14px; text-align: left; font-size: 0.9rem; font-weight: 600; }
  th:first-child { border-radius: 8px 0 0 0; }
  th:last-child { border-radius: 0 8px 0 0; }
  td { padding: 14px; border-bottom: 1px solid #e2e8f0; font-size: 0.95rem; color: #334155; }
  tr:nth-child(even) td { background: #f8fafc; }
  .kriter-ikon { font-size: 1.2rem; margin-right: 8px; vertical-align: middle; }
  .kriter-ad { font-weight: 700; color: #1e293b; }
  .td-puan { text-align: center; font-weight: 800; color: #2563eb; font-size: 1.1rem; }
  .td-max { text-align: center; font-size: 0.85rem; color: #94a3b8; }
  
  .yorum-alani { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 20px; border-radius: 0 8px 8px 0; margin-bottom: 30px; }
  .yorum-baslik { font-size: 0.9rem; font-weight: 800; color: #b45309; margin-bottom: 10px; text-transform: uppercase; }
  .yorum-metin { font-size: 1rem; color: #78350f; line-height: 1.6; font-style: italic; }
  
  .imza-grid { display: flex; justify-content: space-between; margin-top: 40px; text-align: center; }
  .imza-kutu { width: 45%; }
  .imza-cizgi { border-bottom: 1px solid #94a3b8; width: 80%; margin: 40px auto 10px auto; }
  .imza-isim { font-weight: 700; color: #0f172a; }
  .imza-unvan { font-size: 0.85rem; color: #64748b; }
  
  @media print {
      body { background: white; padding: 0; }
      .page { box-shadow: none; margin: 0; border: none; padding: 20px; }
  }
</style>
</head>
<body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam  = int(pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce')) if pd.notna(b.get('Toplam Puan', 0)) else 0
        dinamik = json.loads(str(b.get('Dinamik_JSON', '{}'))) if pd.notna(b.get('Dinamik_JSON', '{}')) else {}

        html += f"""
<div class="page">
    <div class="header">
        <div>
            <div class="kurum-bilgi">{b.get('Okul','')}</div>
            <h1 class="baslik-ana">Öğrenci Performans Karnesi</h1>
            <div class="baslik-alt">{b.get('Ders',ogrt_brans)} &nbsp;|&nbsp; {b.get('Gorev_Turu','Değerlendirme')}</div>
        </div>
        <div class="puan-rozet">
            <div class="puan-deger">{toplam}</div>
            <div class="puan-metin">Toplam Puan</div>
        </div>
    </div>
    
    <div class="ogrenci-karti">
        <div class="bilgi-öğe"><div class="bilgi-etiket">Öğrenci Adı Soyadı</div><div class="bilgi-deger">{b.get('Öğrenci Adı Soyadı','')}</div></div>
        <div class="bilgi-öğe"><div class="bilgi-etiket">Okul Numarası</div><div class="bilgi-deger">{b.get('Okul No','')}</div></div>
        <div class="bilgi-öğe"><div class="bilgi-etiket">Sınıfı / Şubesi</div><div class="bilgi-deger">{b.get('Sınıf','')}</div></div>
        <div class="bilgi-öğe"><div class="bilgi-etiket">Görev Adı</div><div class="bilgi-deger">{b.get('Gorev_Adi','')}</div></div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width: 20%;">Kriter</th>
                <th style="width: 5%; text-align: center;">Max</th>
                <th style="width: 5%; text-align: center;">Puan</th>
                <th style="width: 70%;">Öğretmen Açıklaması</th>
            </tr>
        </thead>
        <tbody>"""

        for k in aktif_kriterler:
            p = dinamik.get(f"{k['id']}_puan", 0)
            a = dinamik.get(f"{k['id']}_aciklama", "-")
            html += f"""
            <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                <td style="padding: 15px; border-right: 1px solid #e2e8f0;">
                    <div style="font-size: 1.1rem; color: #1e3a8a;"><span class="kriter-ikon">{k.get('icon','📌')}</span><strong>{k['baslik']}</strong></div>
                </td>
                <td class="td-max" style="vertical-align: middle; padding: 15px; border-right: 1px solid #e2e8f0;">{k['max']}</td>
                <td style="text-align: center; vertical-align: middle; padding: 15px; border-right: 1px solid #e2e8f0;">
                    <div style="background: #dbeafe; color: #1d4ed8; padding: 8px 12px; border-radius: 8px; font-weight: 900; font-size: 1.2rem; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.05); min-width: 35px;">{p}</div>
                </td>
                <td style="padding: 15px; color: #334155; line-height: 1.6;">{a}</td>
            </tr>"""

        html += f"""
        </tbody>
    </table>
    
    <div class="yorum-alani">
        <div class="yorum-baslik">💬 Öğretmen Genel Değerlendirmesi</div>
        <div class="yorum-metin">"{b.get('Genel Değerlendirme Yorumu','Değerlendirme bekleniyor.')}"</div>
    </div>
    
    <div class="imza-grid">
        <div class="imza-kutu">
            <div class="imza-cizgi"></div>
            <div class="imza-isim">Öğrenci / Veli</div>
            <div class="imza-unvan">Okudum, teslim aldım.</div>
        </div>
        <div class="imza-kutu">
            <div class="imza-cizgi"></div>
            <div class="imza-isim">{ogrt_ad}</div>
            <div class="imza-unvan">{b.get('Ders',ogrt_brans)} Öğretmeni</div>
        </div>
    </div>
</div>"""

    html += "</body></html>"
    return html

def sinif_analiz_raporu(df_sinif, sinif_adi, ogrt_ad):
    df_p = df_sinif.dropna(subset=['Toplam Puan']).copy()
    df_p['Toplam Puan'] = pd.to_numeric(df_p['Toplam Puan'], errors='coerce').fillna(0)

    ortalama  = round(df_p['Toplam Puan'].mean(), 1) if len(df_p) > 0 else 0
    en_yuksek = int(df_p['Toplam Puan'].max())       if len(df_p) > 0 else 0
    en_dusuk  = int(df_p['Toplam Puan'].min())        if len(df_p) > 0 else 0
    puan_0    = len(df_p[df_p['Toplam Puan'] == 0])
    puan_plus = len(df_p[df_p['Toplam Puan'] > 0])
    yukarida  = len(df_p[df_p['Toplam Puan'] >= 85])
    orta_grp  = len(df_p[(df_p['Toplam Puan'] >= 65) & (df_p['Toplam Puan'] < 85)])
    asagida   = len(df_p[df_p['Toplam Puan'] < 65])
    toplam_d  = max(1, puan_plus)
    
    yuzde_basari = round((yukarida + orta_grp) / toplam_d * 100) if toplam_d > 0 else 0

    if ortalama >= 80:
        analiz_renk = "#10b981" 
        analiz_ikon = "🌟"
        analiz_baslik = "Kazanımlar Yüksek Oranda İçselleştirilmiş"
        analiz_metin = f"{sinif_adi} sınıfı, bu görev/konu kapsamında {ortalama} genel ortalama ile üstün bir performans göstermiştir. Öğrencilerin büyük çoğunluğu (%{yuzde_basari}) temel kazanımları başarıyla kavramış ve konuyu öğrenmiştir. Sınıf genelinde öğrenme hedeflerine ulaşılmıştır."
    elif ortalama >= 65:
        analiz_renk = "#f59e0b" 
        analiz_ikon = "📈"
        analiz_baslik = "Kabul Edilebilir Öğrenme Düzeyi, Kısmi Eksikler Var"
        analiz_metin = f"{sinif_adi} sınıfı, bu görevde {ortalama} ortalama ile yeterli bir başarı sergilemiştir. Sınıfın %{yuzde_basari}'lik kesimi konuyu kavramış görünse de, {asagida} öğrencinin kazanımlara ulaşmakta zorlandığı tespit edilmiştir. Alt gruptaki öğrencilere yönelik telafi çalışmaları pekişmeyi sağlayacaktır."
    else:
        analiz_renk = "#ef4444" 
        analiz_ikon = "⚠️"
        analiz_baslik = "Kazanımlarda Eksiklikler ve Anlaşılmayan Noktalar Mevcut"
        analiz_metin = f"{sinif_adi} sınıfının genel ortalamasının {ortalama} düzeyinde kalması, bu konudaki temel kazanımların sınıf genelinde henüz tam olarak yapılandırılamadığını işaret etmektedir. Konunun öğretim stratejisi gözden geçirilerek genel bir konu tekrarı yapılması faydalı olacaktır."

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{sinif_adi} - Başarı Analiz Raporu</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }}
  .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #1e293b; padding-bottom: 20px; margin-bottom: 30px; }}
  .header h1 {{ margin: 0; font-size: 2rem; color: #1e293b; }}
  .header p {{ margin: 5px 0 0; color: #64748b; font-size: 1rem; }}
  
  .ozet-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
  .kutu {{ background: #f1f5f9; padding: 20px; border-radius: 12px; text-align: center; border-top: 4px solid #3b82f6; }}
  .kutu.green {{ border-color: #10b981; }}
  .kutu.red {{ border-color: #ef4444; }}
  .kutu-sayi {{ font-size: 2.5rem; font-weight: 900; color: #1e293b; line-height: 1; }}
  .kutu-etiket {{ font-size: 0.85rem; font-weight: 600; color: #64748b; margin-top: 8px; text-transform: uppercase; }}
  
  .analiz-paneli {{ background: {analiz_renk}15; border-left: 5px solid {analiz_renk}; padding: 25px; border-radius: 8px; margin-bottom: 40px; }}
  .analiz-baslik {{ font-size: 1.2rem; font-weight: 800; color: {analiz_renk}; margin: 0 0 10px 0; }}
  .analiz-metin {{ font-size: 1.05rem; line-height: 1.6; color: #334155; margin: 0; }}
  
  .grafik-alani {{ margin-bottom: 40px; }}
  .grafik-baslik {{ font-size: 1.2rem; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px; }}
  .bar-row {{ display: flex; align-items: center; margin-bottom: 15px; }}
  .bar-etiket {{ width: 200px; font-weight: 600; color: #475569; }}
  .bar-bg {{ flex: 1; background: #e2e8f0; height: 30px; border-radius: 15px; overflow: hidden; position: relative; }}
  .bar-fill {{ height: 100%; display: flex; align-items: center; padding-left: 15px; color: white; font-weight: bold; font-size: 0.9rem; }}
  
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
  th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
  th {{ background: #f8fafc; font-weight: 700; color: #334155; text-transform: uppercase; font-size: 0.85rem; }}
  td.puan {{ font-weight: 800; font-size: 1.1rem; }}
  .durum-badge {{ padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; color: white; }}
  .bg-basarili {{ background: #10b981; }}
  .bg-orta {{ background: #f59e0b; }}
  .bg-gelisim {{ background: #ef4444; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1>{sinif_adi} Başarı Analiz Raporu</h1>
            <p><strong>Öğretmen:</strong> {ogrt_ad} &nbsp;|&nbsp; <strong>Tarih:</strong> {time.strftime('%d.%m.%Y')}</p>
        </div>
    </div>
    
    <div class="ozet-grid">
        <div class="kutu"><div class="kutu-sayi">{len(df_sinif)}</div><div class="kutu-etiket">Sınıf Mevcudu</div></div>
        <div class="kutu green"><div class="kutu-sayi">{ortalama}</div><div class="kutu-etiket">Sınıf Ortalaması</div></div>
        <div class="kutu"><div class="kutu-sayi">{en_yuksek}</div><div class="kutu-etiket">En Yüksek Puan</div></div>
        <div class="kutu red"><div class="kutu-sayi">{en_dusuk}</div><div class="kutu-etiket">En Düşük Puan</div></div>
    </div>

    <div class="analiz-paneli">
        <h3 class="analiz-baslik">{analiz_ikon} Pedagojik Değerlendirme: {analiz_baslik}</h3>
        <p class="analiz-metin">{analiz_metin}</p>
    </div>

    <div class="grafik-alani">
        <div class="grafik-baslik">📊 Öğrenme Düzeyi ve Başarı Dağılımı Grafiği</div>
        
        <div class="bar-row">
            <div class="bar-etiket">🟢 İleri Düzey (85-100)</div>
            <div class="bar-bg">
                <div class="bar-fill" style="width: {round(yukarida/toplam_d*100) if toplam_d else 0}%; background: #10b981;">{yukarida} Öğrenci (%{round(yukarida/toplam_d*100) if toplam_d else 0})</div>
            </div>
        </div>
        
        <div class="bar-row">
            <div class="bar-etiket">🟡 Yeterli Düzey (65-84)</div>
            <div class="bar-bg">
                <div class="bar-fill" style="width: {round(orta_grp/toplam_d*100) if toplam_d else 0}%; background: #f59e0b;">{orta_grp} Öğrenci (%{round(orta_grp/toplam_d*100) if toplam_d else 0})</div>
            </div>
        </div>
        
        <div class="bar-row">
            <div class="bar-etiket">🔴 Destek Gereken (<65)</div>
            <div class="bar-bg">
                <div class="bar-fill" style="width: {round(asagida/toplam_d*100) if toplam_d else 0}%; background: #ef4444;">{asagida} Öğrenci (%{round(asagida/toplam_d*100) if toplam_d else 0})</div>
            </div>
        </div>
    </div>
    
    <div class="grafik-baslik">📋 Detaylı Öğrenci Listesi</div>
    <table>
        <thead>
            <tr><th>No</th><th>Okul No</th><th>Öğrenci Adı Soyadı</th><th>Görev Adı</th><th>Toplam Puan</th><th>Öğrenme Durumu</th></tr>
        </thead>
        <tbody>"""

    df_sorted = df_sinif.copy()
    df_sorted['Toplam Puan'] = pd.to_numeric(df_sorted['Toplam Puan'], errors='coerce').fillna(0)
    df_sorted = df_sorted.sort_values('Toplam Puan', ascending=False)

    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        p = int(row.get('Toplam Puan', 0))
        if p >= 85:
            badge_class = "bg-basarili"
            durum_text = "İleri Düzey"
        elif p >= 65:
            badge_class = "bg-orta"
            durum_text = "Yeterli Düzey"
        else:
            badge_class = "bg-gelisim"
            durum_text = "Destek Gerekiyor"
            
        html += f"""
        <tr>
            <td>{i}</td>
            <td>{row.get('Okul No','')}</td>
            <td><strong>{row.get('Öğrenci Adı Soyadı','')}</strong></td>
            <td>{row.get('Gorev_Adi','')}</td>
            <td class="puan" style="color: {'#10b981' if p>=85 else ('#f59e0b' if p>=65 else '#ef4444')}">{p}</td>
            <td><span class="durum-badge {badge_class}">{durum_text}</span></td>
        </tr>"""

    html += """
        </tbody>
    </table>
</div>
</body>
</html>"""
    return html

def proje_teslim_tutanagi_html(df_sinif, gorev_adi, sinif_adi, ders_adi, ogrt_ad):
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Teslim Tutanağı - {sinif_adi}</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: white; color: black; padding: 20px; }}
    .belge-kutu {{ max-width: 800px; margin: 0 auto; }}
    .baslik {{ text-align: center; border-bottom: 2px solid #1e293b; padding-bottom: 10px; margin-bottom: 20px; }}
    .baslik h2 {{ margin: 0; color: #0f172a; font-size: 1.5rem; text-transform: uppercase; }}
    .baslik p {{ margin: 5px 0 0; font-size: 1.1rem; color: #334155; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px 12px; text-align: left; font-size: 0.95rem; color: #0f172a; }}
    th {{ background-color: #f8fafc; font-weight: bold; text-transform: uppercase; font-size: 0.85rem; }}
    tr:nth-child(even) {{ background-color: #fbfbfc; }}
    .imza-alani {{ text-align: right; margin-top: 50px; font-size: 1.1rem; color: #0f172a; }}
    @media print {{ 
        body {{ padding: 0; }} 
        .belge-kutu {{ max-width: 100%; }}
    }}
</style>
</head>
<body>
    <div class="belge-kutu">
        <div class="baslik">
            <h2>{sinif_adi} Sınıfı Proje / Performans Teslim Tutanağı</h2>
            <p><strong>Ders:</strong> {ders_adi} &nbsp;|&nbsp; <strong>Görev:</strong> {gorev_adi}</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 15%;">Okul No</th>
                    <th style="width: 40%;">Öğrenci Adı Soyadı</th>
                    <th style="width: 20%;">Teslim Tarihi</th>
                    <th style="width: 20%;">İmza</th>
                </tr>
            </thead>
            <tbody>
"""
    for i, (_, row) in enumerate(df_sinif.iterrows(), 1):
        html += f"<tr><td>{i}</td><td>{row['Okul No']}</td><td><strong>{row['Öğrenci Adı Soyadı']}</strong></td><td>..../..../202..</td><td></td></tr>"
        
    html += f"""
            </tbody>
        </table>
        <div class="imza-alani">
            <p><strong>Ders Öğretmeni:</strong> {ogrt_ad}</p>
            <p><strong>İmza:</strong> .......................................</p>
        </div>
    </div>
</body>
</html>
"""
    return html
def toplu_kriterli_liste_html(df_sinif, sinif_adi, ders_adi, ogrt_ad, aktif_kriterler, gorev_adi):
    toplam_ogrenci = len(df_sinif)
    teslim_etmeyenler = 0
    elli_alti = 0
    elli_ustu = 0
    muaf_sayisi = 0

    # 1. Tablo Satırlarını ve Analiz Verilerini Hazırlama
    tablo_satirlari = ""
    for i, (_, row) in enumerate(df_sinif.sort_values(by="Okul No").iterrows(), 1):
        ad_soyad = row.get('Öğrenci Adı Soyadı', '')
        okul_no = row.get('Okul No', '')
        
        # Güvenli puan okuma
        toplam_puan_ham = pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')
        puan = int(toplam_puan_ham) if pd.notna(toplam_puan_ham) else 0
        
        try:
            dinamik = json.loads(str(row.get('Dinamik_JSON', '{}')))
        except:
            dinamik = {}
            
        is_muaf = dinamik.get("muaf", False)
        
        # İlk kriterin puanlanıp puanlanmadığına bakarak teslim/değerlendirme durumunu anlama
        ilk_kriter_id = aktif_kriterler[0]['id'] if aktif_kriterler else "k1"
        degerlendirilmis_mi = f"{ilk_kriter_id}_puan" in dinamik or str(row.get('Genel Değerlendirme Yorumu', '')).strip() != ""

        kriter_hucreleri = ""
        if is_muaf:
            durum = "🚫 Muaf"
            renk = "#64748b"
            kriter_hucreleri = "".join(["<td style='text-align:center; color:#94a3b8;'>-</td>" for _ in aktif_kriterler])
            muaf_sayisi += 1
        elif not degerlendirilmis_mi:
            durum = "❌ Teslim Etmedi / Puanlanmadı"
            renk = "#ef4444"
            kriter_hucreleri = "".join(["<td style='text-align:center; color:#ef4444;'>0</td>" for _ in aktif_kriterler])
            teslim_etmeyenler += 1
        else:
            if puan >= 50:
                durum = "✅ Başarılı"
                renk = "#10b981"
                elli_ustu += 1
            else:
                durum = "⚠️ Geliştirilmeli (<50)"
                renk = "#f59e0b"
                elli_alti += 1
                
            for k in aktif_kriterler:
                k_puan = dinamik.get(f"{k['id']}_puan", 0)
                kriter_hucreleri += f"<td style='text-align:center;'>{k_puan}</td>"

        tablo_satirlari += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="text-align:center;">{i}</td>
            <td style="text-align:center;">{okul_no}</td>
            <td><strong>{ad_soyad}</strong></td>
            {kriter_hucreleri}
            <td style="text-align:center; font-weight:900; color:{renk}; font-size:1.1rem;">{puan}</td>
            <td style="color:{renk}; font-weight:bold;">{durum}</td>
        </tr>
        """

    # 2. Rapor Analiz Metnini Üretme
    degerlendirilen = elli_ustu + elli_alti
    basari_yuzdesi = round((elli_ustu / degerlendirilen * 100)) if degerlendirilen > 0 else 0
    
    analiz_metni = f"Bu rapora göre, <strong>{sinif_adi}</strong> sınıfındaki toplam <strong>{toplam_ogrenci}</strong> öğrenciden <strong>{teslim_etmeyenler}</strong> öğrenci ödev/proje teslim etmemiştir. "
    if muaf_sayisi > 0: analiz_metni += f"<strong>{muaf_sayisi}</strong> öğrenci görevden muaf tutulmuştur. "
    
    if degerlendirilen > 0:
        analiz_metni += f"Değerlendirmeye katılan {degerlendirilen} öğrencinin <strong>{elli_alti}</strong> tanesi 50 puanlık başarı barajının altında kalmıştır. Sınıfın projeye/göreve dayalı genel başarı oranı <strong>%{basari_yuzdesi}</strong> olarak gerçekleşmiştir. "
        
        if basari_yuzdesi >= 80: analiz_metni += "Sınıf genel olarak yüksek bir performans sergilemiş ve hedeflenen kazanımlara ulaşılmıştır."
        elif basari_yuzdesi >= 50: analiz_metni += "Sınıf ortalama bir performans sergilemiş olup, 50 puan altı alan öğrenciler için telafi veya destekleyici çalışmalar planlanmalıdır."
        else: analiz_metni += "Sınıfın büyük çoğunluğu barajın altında kalmıştır. Konunun genel tekrarı veya proje/performans yönergelerinin gözden geçirilmesi pedagojik olarak tavsiye edilir."
    else:
        analiz_metni += "Henüz puanlanmış bir öğrenci bulunmamaktadır."

    # 3. HTML Kodu
    kriter_basliklari = "".join([f"<th style='text-align:center; width:8%; font-size:0.8rem;'>{k['baslik']}<br><span style='color:#64748b; font-weight:normal;'>(Maks: {k['max']})</span></th>" for k in aktif_kriterler])

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>{sinif_adi} - Toplu Kriter Dağılım Listesi</title>
<style>
    @page {{ size: landscape; margin: 15mm; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: white; color: #0f172a; font-size: 11px; }}
    .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #1e293b; padding-bottom: 10px; }}
    .header h2 {{ margin: 0; font-size: 1.4rem; color: #1e3a8a; text-transform: uppercase; }}
    .header p {{ margin: 5px 0 0; color: #475569; font-size: 1rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; table-layout: auto; word-wrap: break-word; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 6px; }}
    th {{ background: #f8fafc; color: #1e293b; font-weight: 800; }}
    .analiz-kutusu {{ background: #f0f9ff; border-left: 5px solid #2563eb; padding: 15px; border-radius: 8px; font-size: 1rem; line-height: 1.5; color: #1e3a8a; margin-bottom: 30px; }}
    .imza-alani {{ display: flex; justify-content: space-between; margin-top: 40px; font-size: 1.1rem; }}
    .imza-kutu {{ text-align: center; width: 30%; }}
    @media print {{ .no-print {{ display: none !important; }} }}
</style>
</head>
<body>
    <div class="no-print" style="text-align:center; padding:12px; background:#f1f5f9; margin-bottom:15px; border-radius:8px; border:1px solid #cbd5e1;">
        <strong style="color:#1e293b; margin-right:15px;">⚙️ Sayfa Sığdırma Ayarları:</strong>
        <button onclick="ayarla('font', 1)" style="cursor:pointer; padding:5px 10px; margin:0 3px;">A+ Yazıyı Büyüt</button>
        <button onclick="ayarla('font', -1)" style="cursor:pointer; padding:5px 10px; margin:0 3px;">A- Yazıyı Küçült</button>
        <button onclick="ayarla('pad', 2)" style="cursor:pointer; padding:5px 10px; margin:0 3px;">↕️ Satır Genişlet</button>
        <button onclick="ayarla('pad', -2)" style="cursor:pointer; padding:5px 10px; margin:0 3px;">>< Satır Daralt</button>
    </div>
    <script>
        let vals = {{ font: 11, pad: 6 }};
        function ayarla(tip, yon) {{
            vals[tip] += yon;
            if(vals.pad < 0) vals.pad = 0;
            let elements = document.querySelectorAll('td, th, .yorum-metin, .bilgi-deger, .kriter-ad');
            elements.forEach(el => {{
                if(tip === 'font') el.style.fontSize = vals.font + 'px';
                if(tip === 'pad' && (el.tagName === 'TD' || el.tagName === 'TH')) {{
                    el.style.paddingTop = vals.pad + 'px';
                    el.style.paddingBottom = vals.pad + 'px';
                }}
            }});
        }}
    </script>
    
    <div class="header">
        <h2>{sinif_adi} SINIFI TOPLU PROJE/PERFORMANS DEĞERLENDİRME ÇİZELGESİ</h2>
        <p><strong>Ders:</strong> {ders_adi} &nbsp;|&nbsp; <strong>Görev:</strong> {gorev_adi}</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width:3%; text-align:center;">#</th>
                <th style="width:5%; text-align:center;">No</th>
                <th style="width:auto; text-align:left;">Öğrenci Adı Soyadı</th>
                {kriter_basliklari}
                <th style="width:7%; text-align:center;">Toplam</th>
                <th style="width:12%; text-align:center;">Durum</th>
            </tr>
        </thead>
        <tbody>
            {tablo_satirlari}
        </tbody>
    </table>

    <div class="analiz-kutusu">
        <strong>📈 İdare İçin Dönem Sonu Performans Analizi:</strong><br>
        {analiz_metni}
    </div>

    <div class="imza-alani">
        <div class="imza-kutu">
            <br>Öğretmen
            <br><strong>{ogrt_ad}</strong>
        </div>
        <div class="imza-kutu">
            Tasdik Olunur<br>Okul Müdürü<br>
            <strong>........................................</strong>
        </div>
    </div>
</body>
</html>"""
    return html
</script>
<style>
    @media print { .no-print { display: none !important; } }
    table { table-layout: auto; width: 100%; word-wrap: break-word; }
</style>
    <div class="header">
        <h2>{sinif_adi} SINIFI TOPLU PROJE/PERFORMANS DEĞERLENDİRME ÇİZELGESİ</h2>
        <p><strong>Ders:</strong> {ders_adi} &nbsp;|&nbsp; <strong>Görev:</strong> {gorev_adi}</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width:3%; text-align:center;">#</th>
                <th style="width:5%; text-align:center;">No</th>
                <th style="width:auto; text-align:left;">Öğrenci Adı Soyadı</th>
                {kriter_basliklari}
                <th style="width:7%; text-align:center;">Toplam</th>
                <th style="width:12%; text-align:center;">Durum</th>
            </tr>
        </thead>
        <tbody>
            {tablo_satirlari}
        </tbody>
    </table>

    <div class="analiz-kutusu">
        <strong>📈 İdare İçin Dönem Sonu Performans Analizi:</strong><br>
        {analiz_metni}
    </div>

    <div class="imza-alani">
        <div class="imza-kutu">
            <br>Öğretmen
            <br><strong>{ogrt_ad}</strong>
        </div>
        <div class="imza-kutu">
            Tasdik Olunur<br>Okul Müdürü<br>
            <strong>........................................</strong>
        </div>
    </div>
</body>
</html>"""
    
    return html
# ==========================================
# 10. YAPAY ZEKA BAĞLANTILARI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans, ogrt_api_key=""):
    api_url = get_gemini_api_url(ogrt_api_key)
    if not api_url: return {"genel": "Sistemde API Anahtarı bulunamadı."}

    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye    = "".join(filter(str.isdigit, sinif_str)) or "7"
    ogrenci_isim = isme_hitap_et(bilgi_dict.get('Öğrenci Adı Soyadı', 'Öğrenci'))
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])

    prompt = f"""Sen profesyonel bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}. {seviye}. Sınıf öğrencin sevgili {ogrenci_isim}'i değerlendiriyorsun.
Lütfen öğrenciye doğrudan 'Sevgili {ogrenci_isim}, ...' şeklinde hitap ederek şefkatli, pedagojik ve motive edici konuş. (Öğrencinin soyadını asla kullanma).

DEĞERLENDİRİLEN KONU / ÖĞRETMENİN NOTU: "{ham_metin}"
Bu konuyu ve öğretmenin notunu dikkate alarak açıklamaları yaz.
Değerlendirme Kriterleri:\n{kriter_ozeti}\nGÖREV MODU: """

    if mod == "A":
        prompt += f"""YORUMDAN PUAN ÜRETME. Yukarıda verilen nota göre pedagojik açıklamalar yaz ve mantıklı puanlar belirle."""
    elif mod == "B":
        prompt += f"""HEDEF PUANDAN YORUM ÜRETME. Hedef: {hedef_puan}/100\nBu puana ulaşacak şekilde kriterlere puan dağıt ve yukarıdaki konuya uygun açıklamalar yaz."""
    else:
        ozet = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA. Öğretmen puanları verdi:\n{ozet}\nSadece yukarıdaki konuya uygun pedagojik açıklamalar yaz. PUANLARI DEĞİŞTİRME."""

    prompt += """\nEKSTRA: "genel" anahtarında öğrenciye ("Sevgili İsim, ...") hitap eden motive edici genel bir yorum yaz.
SADECE JSON:\n{ "puanlar": { "k1": 40 }, "aciklamalar": { "k1": "..." }, "genel": "Sevgili..." }"""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    r = requests.post(api_url, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw.replace("```json", "").replace("```", "").strip())

def ai_karne_gorusu_yaz(tam_isim, sinifi, notlar_sozlugu, ekstra_gozlem, ogrt_ad, ogrt_api_key=""):
    api_url = get_gemini_api_url(ogrt_api_key)
    if not api_url: return "Sistemde API Anahtarı bulunamadı."

    ogrenci_isim = isme_hitap_et(tam_isim)
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if str(notu).strip() != ""])
    
    davranis_puani = notlar_sozlugu.get("Davranış", 100)
    try: d_puan = float(str(davranis_puani).replace(",", "."))
    except: d_puan = 100.0
        
    davranis_uyarisi = "Öğrencinin davranış notu 50'nin altında. Lütfen yapıcı ve pedagojik bir uyarıda bulun." if d_puan < 50 else "Öğrencinin davranış notu gayet iyi. Bu olumlu tutumunu takdir et."

    prompt = f"""Sınıf öğretmeni {ogrt_ad} olarak {sinifi} sınıfından {ogrenci_isim} adlı öğrenciye e-okul karne görüşü yaz.
Öğrencinin Ders Notları ve Davranış Puanı (Hepsi 100 Üzerindendir):
{notlar_metni}
Ekstra Öğretmen Gözlemi: {ekstra_gozlem}
ÖZEL TALİMAT: {davranis_uyarisi}
Lütfen 'Sevgili {ogrenci_isim}' diye hitap eden, 3-4 cümlelik bir dönem sonu karne görüşü üret."""
    
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    r = requests.post(api_url, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ==========================================
# 11. ÖĞRENCİ SORGULAMA EKRANI (PREMIUM DASHBOARD)
# ==========================================
def ogrenci_sorgu_ekrani(df, ayarlar):
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 30px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);">
        <h1 style="margin:0; font-size: 2.2rem; font-weight: 800;">🎓 Öğrenci Gelişim ve Performans Paneli</h1>
        <p style="font-size: 1.05rem; opacity: 0.9; margin-top: 5px;">Dönem sonu değerlendirmelerinize ve proje sonuçlarınıza buradan ulaşabilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔍 Sisteme Giriş Yapın</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 1.5, 1])
    okul_listesi = sorted(df['Okul'].dropna().unique().tolist()) if not df.empty else []
    s_okul  = col1.selectbox("🏫 Okulunuz", ["— Okul Seçiniz —"] + okul_listesi)
    
    sinif_listesi = sorted(df[df['Okul'] == s_okul]['Sınıf'].dropna().unique().tolist()) if s_okul != "— Okul Seçiniz —" else []
    s_sinif = col2.selectbox("📚 Sınıfınız", ["— Sınıf —"] + sinif_listesi if sinif_listesi else ["Önce okul seçin"])
    
    s_no = col3.text_input("🔢 Okul Numaranız", placeholder="Örn: 1453")

    if st.button("🚀 Performans Sonuçlarımı Göster", use_container_width=True, type="primary"):
        if s_okul == "— Okul Seçiniz —" or not s_no.strip():
            st.warning("Giriş yapabilmek için lütfen okulunuzu ve numaranızı eksiksiz girin.")
        else:
            filtre = (df['Okul'] == s_okul) & (df['Okul No'] == s_no.strip())
            if s_sinif not in ["— Sınıf —", "Önce okul seçin"]:
                filtre = filtre & (df['Sınıf'] == s_sinif)
            
            # Öğrenci "Muaf" işaretlenmişse sonuçlarda gösterme
            def muaf_mi_ogrenci(json_str):
                try: return json.loads(str(json_str)).get("muaf", False)
                except: return False
            
            sonuclar = df[filtre].copy()
            sonuclar = sonuclar[~sonuclar['Dinamik_JSON'].apply(muaf_mi_ogrenci)]

            if sonuclar.empty:
                st.error("❌ Sisteme kayıtlı, değerlendirilmiş bir göreviniz bulunamadı.")
            else:
                ogrenci_adi = sonuclar.iloc[0]['Öğrenci Adı Soyadı']
                st.markdown(f"""
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 5px solid #10b981;">
                    <h3 style="margin: 0; color: #166534;">Hoş geldin, {ogrenci_adi}! 🌟</h3>
                    <p style="margin: 5px 0 0; color: #15803d; font-size: 0.95rem;">Aşağıda değerlendirmesi tamamlanan <strong>{len(sonuclar)}</strong> adet proje ve performans görevin listelenmektedir.</p>
                </div>
                """, unsafe_allow_html=True)

                col_dl1, col_dl2 = st.columns(2)
                toplu_html = ogrenci_karnesi_html_uret(sonuclar, ayarlar)
                col_dl1.download_button("📥 Tüm Karnelerimi Tek Dosyada İndir", data=toplu_html, file_name=f"{ogrenci_adi}_Tum_Karneler.html", mime="text/html", use_container_width=True)

                st.markdown("### 📊 Detaylı Değerlendirme Raporları")
                
                for idx, row in sonuclar.iterrows():
                    toplam_val = pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')
                    p = int(toplam_val) if pd.notna(toplam_val) else 0
                    
                    renk = "#10b981" if p >= 85 else ("#f59e0b" if p >= 65 else "#ef4444")
                    durum_metni = "Çok Başarılı" if p >= 85 else ("Gelişimi İyi" if p >= 65 else "Desteklenmeli")
                    
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 15px;">
                            <div>
                                <div style="color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase;">{row['Ders']} | {row.get('Gorev_Turu','')}</div>
                                <h3 style="margin: 5px 0 0; color: #0f172a;">{row['Gorev_Adi']}</h3>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 2.2rem; font-weight: 900; color: {renk}; line-height: 1;">{p}</div>
                                <div style="font-size: 0.8rem; font-weight: 700; color: #64748b; background: #f1f5f9; padding: 3px 10px; border-radius: 12px; margin-top: 5px;">{durum_metni}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if row.get('Genel Değerlendirme Yorumu'):
                        st.markdown(f"""
                        <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                            <strong style="color: #b45309;">Öğretmen Görüşü:</strong><br>
                            <span style="color: #78350f; font-style: italic;">"{row['Genel Değerlendirme Yorumu']}"</span>
                        </div>
                        """, unsafe_allow_html=True)

                    dinamik = {}
                    try:
                        if pd.notna(row.get('Dinamik_JSON', '')):
                            dinamik = json.loads(str(row['Dinamik_JSON']))
                    except: pass

                    if dinamik:
                        with st.expander("🔍 Puan Detaylarını ve Kriterleri İncele"):
                            for k_id in [k.replace("_puan","") for k in dinamik if k.endswith("_puan")]:
                                baslik, maks, icon = kriter_bul(k_id, ayarlar)
                                kp = dinamik.get(f"{k_id}_puan", 0)
                                ka = dinamik.get(f"{k_id}_aciklama", "-")
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; align-items:flex-start; padding:8px 0; border-bottom:1px dashed #e2e8f0;">
                                    <div style="flex:1;"><strong>{icon} {baslik}</strong><br><span style="font-size:0.85rem; color:#64748b;">{ka}</span></div>
                                    <div style="font-weight:800; color:#2563eb; margin-left:15px;">{kp} <span style="font-size:0.75rem; color:#94a3b8;">/ {maks}</span></div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            tekil_html = ogrenci_karnesi_html_uret(sonuclar, ayarlar, tekil_gorev_idx=idx)
                            st.download_button("📥 Bu Görevin Detaylı Çıktısını Al", data=tekil_html, file_name=f"{ogrenci_adi}_{row['Ders']}_Detay.html", mime="text/html", key=f"dl_tek_{idx}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 12. GİRİŞ EKRANI
# ==========================================
def giris_ekrani(df, ayarlar):
    tab_ogr, tab_ogrt = st.tabs(["🎓 Öğrenci ve Veli Girişi", "👨‍🏫 Öğretmen / İdare Girişi"])

    with tab_ogr:
        ogrenci_sorgu_ekrani(df, ayarlar)

    with tab_ogrt:
        c1, c2, c3 = st.columns([1, 1.8, 1])
        with c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            g1, g2, g3 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol", "🔑 Şifremi Unuttum"])

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

            with g2:
                st.markdown("##### 📍 Kurum Bilgileri")
                st.info("💡 Lütfen önce okulunuzun listede olup olmadığını kontrol edin. Aynı okulun 2 farklı isimle kaydedilmemesi için, sadece listede YOKSA 'Yeni Okul Ekle' seçeneğini kullanın.")
                
                sec_il = st.selectbox("İl Seçiniz", ["— Seçiniz —"] + TUM_ILLER)
                
                sec_ilce = "— Seçiniz —"
                if sec_il and sec_il != "— Seçiniz —":
                    sec_ilce = st.text_input(f"{sec_il} - İlçe Adını Yazınız (Örn: Çankaya)").strip().title()

                sec_okul = "— Seçiniz —"
                if sec_ilce:
                    sec_okul = st.selectbox("Okulunuzu Seçiniz", ["— Seçiniz —", "➕ Yeni Okul Ekle"] + sorted(ayarlar["okullar"]))
                    if sec_okul == "➕ Yeni Okul Ekle":
                        sec_okul_yeni = st.text_input("Okulun Adını Yazınız (Örn: Süleyman Demirel İlkokulu)").strip().title()
                        if sec_okul_yeni:
                            sec_okul = f"{sec_il} / {sec_ilce} / {sec_okul_yeni}"

                st.markdown("##### 👤 Kişisel Bilgiler")
                r_ad     = st.text_input("Ad Soyad", key="r_ad")
                r_brans  = st.text_input("Branş", key="r_brans")
                r_eposta = st.text_input("E-posta Adresiniz", key="r_eposta", placeholder="ornek@gmail.com")
                r_kadi   = st.text_input("Kullanıcı Adı Seçin", key="r_kadi")
                r_sifre  = st.text_input("Şifre Belirleyin", type="password", key="r_sifre")

                mevcut_ogrt = any(
                    str(v.get("ad","")).strip().lower() == str(r_ad).strip().lower()
                    and v.get("okul") == sec_okul
                    for v in ayarlar["kullanicilar"].values()
                )

                if st.button("Kayıt Ol", use_container_width=True, key="btn_kayit"):
                    if r_kadi in ayarlar["kullanicilar"]:
                        st.error("Bu kullanıcı adı alınmış.")
                    elif mevcut_ogrt:
                        st.error("⚠️ Sistemde bu okulda adınıza açılmış bir kayıt zaten mevcut!")
                        st.info("Okul idaresi veya sistem yöneticisi sizi sisteme önceden eklemiş olabilir. Lütfen şifrenizi onlardan talep ediniz.")
                    elif not (r_kadi and r_sifre and r_ad and sec_okul and "Seçiniz" not in sec_okul):
                        st.warning("Lütfen il, ilçe, okul ve tüm kişisel alanları doldurun.")
                    else:
                        if sec_okul not in ayarlar["okullar"]:
                            ayarlar["okullar"].append(sec_okul)

                        is_auto = ayarlar.get("otomatik_onay", True)
                        ayarlar["kullanicilar"][r_kadi] = {
                            "sifre": r_sifre, "rol": "ogretmen", "ad": r_ad,
                            "okul": sec_okul, "brans": r_brans, "eposta": r_eposta, "onayli": is_auto
                        }
                        ayar_kaydet(ayarlar)
                        if is_auto:
                            st.success("✅ Kayıt başarılı! Giriş yapabilirsiniz.")
                        else:
                            st.success("⏳ Kayıt alındı. Yönetici onayından sonra giriş yapabilirsiniz.")

            with g3:
                st.markdown("E-posta adresinize yeni şifre gönderilecektir.")
                u_eposta = st.text_input("Kayıtlı E-posta Adresiniz", key="u_eposta")
                if st.button("🔑 Yeni Şifre Gönder", use_container_width=True, key="btn_sifre"):
                    bulunan, bulunan_kadi = None, None
                    for kadi, user in ayarlar["kullanicilar"].items():
                        if user.get("eposta","").strip().lower() == u_eposta.strip().lower():
                            bulunan, bulunan_kadi = user, kadi
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
        • Sistemde idare tarafından daha önce kaydınız açılmışsa mükerrer kayıt yapamazsınız. Şifrenizi idareden isteyin.<br>
        • Yönetici otomatik onayı açmışsa direkt giriş yapabilirsiniz; kapalıysa yönetici onayını bekleyin.
        </div></div>
        <div class="kilavuz-item">
        <div class="kilavuz-baslik">2️⃣ Değerlendirme Ölçeği (Şablon) Yönetimi</div>
        <div class="kilavuz-icerik">
        • Ayarlar & Profil → Ölçek/Şablon sekmesinden kendi şablonunuzu oluşturun.<br>
        • Toplam puan her zaman 100 olmalıdır. Excel ile de şablon yükleyebilirsiniz.<br>
        • Sadece kendi oluşturduğunuz şablonları silebilirsiniz.
        </div></div>
        <div class="kilavuz-item">
        <div class="kilavuz-baslik">3️⃣ Öğrenci Listesi Yükleme</div>
        <div class="kilavuz-icerik">
        • <b>Öğrenci & Görev → Excel ile Yükle</b> sekmesinden şablonu indirin, doldurun ve yükleyin.<br>
        • Mükerrer kayıt koruma sistemi otomatik çalışır.
        </div></div>
        <div class="kilavuz-item">
        <div class="kilavuz-baslik">4️⃣ Yapay Zeka Değerlendirme</div>
        <div class="kilavuz-icerik">
        • <b>AI Değerlendirme</b> sekmesinde öğrenci ve görevi seçin, şablon belirleyin.<br>
        • <b>Mod A:</b> Yorum gir → AI puanlasın &nbsp;|&nbsp; <b>Mod B:</b> Hedef puan ver → AI dağıtsın &nbsp;|&nbsp; <b>Mod C:</b> Manuel puan → AI açıklasın.
        </div></div>
        <div class="kilavuz-item">
        <div class="kilavuz-baslik">5️⃣ Raporlar ve Karneler</div>
        <div class="kilavuz-icerik">
        • <b>Raporlar → Sınıf Raporları</b> sekmesinden HTML karne ve analiz raporu indirin.<br>
        • Silmeden önce <b>Raporlar → Veri Yedekleme</b> bölümünden Excel yedeği alın.
        </div></div>
        """, unsafe_allow_html=True)

# ==========================================
# 14. ŞABLON YÖNETİM MODÜLÜ
# ==========================================
def sablon_yonetimi_ui(ayarlar, kb, rol):
    st.markdown("#### 📐 Değerlendirme Ölçeği (Şablon) Yönetimi")
    st.info("Kriterlerin toplam puanı 100 olmalıdır.")

    t_man, t_ex = st.tabs(["✍️ Manuel Oluştur", "📥 Excel ile Yükle"])

    with t_man:
        if "t_df" not in st.session_state:
            st.session_state["t_df"] = pd.DataFrame([{"Başlık": "İçerik", "Puan": 50, "Açıklama": ""}])
        s_isim_yeni = st.text_input("Ölçek/Şablon Adı", key=f"man_sablon_ad_{rol}")
        e_df = st.data_editor(st.session_state["t_df"], num_rows="dynamic", use_container_width=True, key=f"man_editor_{rol}")
        if st.button("💾 Manuel Ölçeği Kaydet", key=f"btn_man_kaydet_{rol}"):
            if pd.to_numeric(e_df["Puan"], errors="coerce").sum() == 100 and s_isim_yeni:
                tam_isim = s_isim_yeni if rol == "admin" else f"{s_isim_yeni} (Ekleyen: {kb['ad']})"
                n_k = [{"id": f"k{i+1}", "baslik": str(r["Başlık"]), "max": int(r["Puan"]),
                         "icon": "📌", "aciklama": str(r.get("Açıklama",""))} for i, r in e_df.iterrows()]
                ayarlar["sablonlar"][tam_isim] = n_k
                ayar_kaydet(ayarlar)
                st.success(f"✅ '{tam_isim}' eklendi!")
                st.rerun()
            else:
                st.error("Toplam puan 100 olmalı ve bir isim girilmelidir!")

    with t_ex:
        sab_ex_df = pd.DataFrame(columns=["Kriter Başlığı", "Maksimum Puan", "Açıklama"])
        out_sab = io.BytesIO()
        with pd.ExcelWriter(out_sab, engine='xlsxwriter') as w:
            sab_ex_df.to_excel(w, index=False, sheet_name="Olcek")
            w.sheets['Olcek'].set_column(0, 2, 30)
        st.download_button("📄 Excel Ölçek Şablonunu İndir", data=out_sab.getvalue(),
                           file_name="Olcek_Sablonu.xlsx", key=f"dl_sab_{rol}")

        up_sab      = st.file_uploader("Doldurulmuş Ölçek Excelini Yükle", type=["xlsx"], key=f"up_sab_{rol}")
        up_sab_isim = st.text_input("Yüklenen Ölçeğin Adı", key=f"up_sab_ad_{rol}")
        if st.button("🚀 Excel'den Ölçeği Kaydet", key=f"btn_ex_kaydet_{rol}"):
            if up_sab and up_sab_isim:
                try:
                    sdf = pd.read_excel(up_sab)
                    if pd.to_numeric(sdf.iloc[:, 1], errors="coerce").sum() == 100:
                        tam_isim = up_sab_isim if rol == "admin" else f"{up_sab_isim} (Ekleyen: {kb['ad']})"
                        n_k = [{"id": f"k{i+1}", "baslik": str(r.iloc[0]), "max": int(r.iloc[1]),
                                  "icon": "📌", "aciklama": str(r.iloc[2]) if len(r) > 2 else ""}
                                 for i, r in sdf.iterrows()]
                        ayarlar["sablonlar"][tam_isim] = n_k
                        ayar_kaydet(ayarlar)
                        st.success("✅ Ölçek başarıyla yüklendi!")
                        st.rerun()
                    else:
                        st.error("Kriterlerin toplam puanı 100 olmalıdır!")
                except Exception as e:
                    st.error(f"Hata: {e}")
            else:
                st.warning("Lütfen dosyayı yükleyin ve isim belirleyin.")

    st.markdown("#### 🗑️ Ölçek Sil")
    if rol == "admin":
        silinebilir = [s for s in ayarlar["sablonlar"] if "Varsayılan" not in s]
    else:
        silinebilir = [s for s in ayarlar["sablonlar"] if f"(Ekleyen: {kb['ad']})" in s]

    if silinebilir:
        sil_sablon = st.selectbox("Silinecek Şablon", silinebilir, key=f"sil_sab_{rol}")
        if st.button("🗑️ Seçili Ölçeği Sil", key=f"btn_sil_sab_{rol}"):
            del ayarlar["sablonlar"][sil_sablon]
            ayar_kaydet(ayarlar)
            st.success("Silindi.")
            st.rerun()
    else:
        st.info("Silinebilecek (yetkiniz olan) bir şablon bulunmuyor.")


# ==========================================
# 15. YÖNETİM PANELİ (Geçmiş Düzenleme ve Kalıcı E-Okul Eklendi)
# ==========================================
def yonetim_paneli(df, ayarlar):
    _init_nav()

    aktif_id    = st.session_state["aktif_kullanici"]
    kb          = st.session_state["kullanici_bilgi"]
    rol         = kb["rol"]
    admin_bakis = st.session_state.get("admin_bakis_modu", False)
    admin_bakis_ogrt = st.session_state.get("admin_bakis_ogretmen", None)

    # ── Profil çubuğu ──
    col_profil1, col_profil2 = st.columns([4, 1])
    with col_profil1:
        admin_etiket  = '<span style="color:#ef4444;font-weight:800;">🔴 ADMİN</span>' if rol == 'admin' and not admin_bakis else ''
        gozatma_badge = (f'<span style="background:#fef9c3;color:#854d0e;padding:2px 10px;'
                         f'border-radius:6px;font-size:0.75rem;margin-left:8px;">👁 GÖZATMA → {admin_bakis_ogrt}</span>'
                         if admin_bakis else '')
        st.markdown(f"""
        <div style="background:white; padding:14px 22px; border-radius:12px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:16px; border-left: 5px solid #2563eb;">
            <div>
                <div style="font-size:1.15rem;font-weight:900;color:#1e293b;">
                    {'👁️ ' if admin_bakis else '👋 '}{kb['ad']} {gozatma_badge}
                </div>
                <div style="font-size:0.88rem;color:#64748b;font-weight:600;margin-top:2px;">
                    {kb.get('okul','') or 'Yönetici'} &nbsp;|&nbsp; {kb.get('brans','')} {admin_etiket}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_profil2:
        if admin_bakis:
            if st.button("← Admin'e Dön", use_container_width=True):
                st.session_state["admin_bakis_modu"] = False
                st.session_state["admin_bakis_ogretmen"] = None
                st.rerun()
        else:
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                st.session_state.clear()
                st.rerun()

    # ── Yetkili veri filtresi ──
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

    # ── Ana navigasyon çubuğu ──
    render_ana_nav(rol, admin_bakis)
    aktif_ana = st.session_state.get("nav_ana", "ogr_gorev")

    # ══════════════════════════════════════════════════
    # SEKME: ÖĞRENCİ & GÖREV
    # ══════════════════════════════════════════════════
    if aktif_ana == "ogr_gorev":
        render_nav_bar(ALT_MENU_OGR_GOREV, "nav_ogr_alt", is_main=False)
        aktif_ogr = st.session_state.get("nav_ogr_alt", "excel_yukle")

        # ── Excel ile Yükle ──
        if aktif_ogr == "excel_yukle":
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>📥 Excel ile Toplu Görev Tanımla</div>", unsafe_allow_html=True)
            h_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul Seçin", sorted(ayarlar["okullar"]), key="ex_okul")

            hedef_ogrt_ex  = aktif_id
            kb_aktif       = kb if not admin_bakis else ayarlar["kullanicilar"].get(admin_bakis_ogrt, kb)

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

            g_tur  = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"])
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
                        excel_df = excel_df.fillna("") 
                        cols = excel_df.columns
                        no_col    = next((c for c in cols if "no" in str(c).lower()), cols[0])
                        ad_col    = next((c for c in cols if "ad" in str(c).lower()), cols[1] if len(cols) > 2 else cols[0])
                        sinif_col = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols) > 2 else None)

                        db_records = []
                        for _, row in excel_df.iterrows():
                            o_no = str(row[no_col]).strip().replace('.0', '')
                            if not o_no or o_no.lower() == "nan": continue
                            
                            kontrol = df[(df['Okul'] == h_okul) & (df['Okul No'] == o_no) &
                                         (df['Gorev_Adi'] == g_isim.strip()) & (df['Atanan_Ogretmen'] == hedef_ogrt_ex)]
                            if kontrol.empty:
                                target_ders = (kb_aktif.get("brans","Genel") if hedef_ogrt_ex == aktif_id
                                               else ayarlar["kullanicilar"].get(hedef_ogrt_ex,{}).get("brans","Genel"))
                                sinif_val   = str(row[sinif_col]) if sinif_col and str(row[sinif_col]).strip() != "" else "Bilinmiyor"
                                db_records.append({
                                    'okul': h_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': hedef_ogrt_ex,
                                    'ders': target_ders, 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col],
                                    'sinif': sinif_val, 'gorev_turu': g_tur, 'gorev_adi': g_isim.strip(), 'dinamik_json': {}
                                })
                        if db_records:
                            supabase.table('gorevler').insert(db_records).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(db_records)} öğrenciye '{g_isim}' görevi tanımlandı!")
                            time.sleep(1); st.rerun()
                        else:
                            st.warning("Geçerli bir öğrenci bulunamadı veya görev daha önce bu öğrencilere atanmış.")
                    except Exception as e:
                        st.error(f"Hata: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tekil Ekle ──
        elif aktif_ogr == "tekil_ekle":
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>➕ Tekil Öğrenci/Görev Ekle</div>", unsafe_allow_html=True)
            with st.form("tekil_ekle_form"):
                m_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]))
                hedef_ogrt_man = aktif_id
                if rol == "admin" and not admin_bakis:
                    ogrt_listesi_man = {k: f"{v['ad']} ({v.get('okul','-')})" for k, v in ayarlar["kullanicilar"].items()
                                        if v.get("rol") == "ogretmen" and v.get("onayli", True)}
                    hedef_ogrt_man = st.selectbox(
                        "Öğretmen", ["admin"] + list(ogrt_listesi_man.keys()),
                        format_func=lambda x: "Yönetici" if x == "admin" else ogrt_listesi_man[x]
                    )
                col_m1, col_m2, col_m3 = st.columns(3)
                m_no    = col_m1.text_input("Okul No")
                m_ad    = col_m2.text_input("Ad Soyad")
                m_sinif = col_m3.text_input("Sınıf")
                m_gtur  = st.selectbox("Görev Türü", ["Proje", "Performans"])
                m_gadi  = st.text_input("Görev Adı")
                
                if st.form_submit_button("➕ Ekle ve Kaydet"):
                    if m_no and m_ad and m_gadi:
                        target_ders_man = (kb.get("brans","") if hedef_ogrt_man == aktif_id
                                           else ayarlar["kullanicilar"].get(hedef_ogrt_man,{}).get("brans",""))
                        supabase.table('gorevler').insert({
                            'okul': m_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': hedef_ogrt_man,
                            'ders': target_ders_man, 'okul_no': m_no.strip(), 'ogrenci_adi_soyadi': m_ad,
                            'sinif': m_sinif, 'gorev_turu': m_gtur, 'gorev_adi': m_gadi, 'dinamik_json': {}
                        }).execute()
                        st.cache_data.clear()
                        st.success("✅ Eklendi!")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("Okul no, ad ve görev adı zorunludur.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Havuzdan Görev Ata ──
        elif aktif_ogr == "havuz_ata":
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>🏫 Havuzdaki Sınıflara Yeni Görev Ata</div>", unsafe_allow_html=True)
            st.markdown('<div class="info-banner">Okulunuzdaki diğer öğretmenlerin yüklediği sınıfları seçerek kendi dersiniz için görev tanımlayabilirsiniz.</div>', unsafe_allow_html=True)

            islem_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]), key="havuz_okul")
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
                g_tur_h  = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"], key="gth")
                g_isim_h = st.text_input("Görevin Adı", key="gih", placeholder="Örn: Matematik Dönem Projesi")

                if st.button("🚀 Seçili Sınıflara Görevi Ata", use_container_width=True):
                    if not secilen_siniflar or not g_isim_h.strip():
                        st.error("Sınıf seçin ve görev adı girin.")
                    else:
                        pool_students = df[(df['Okul'] == islem_okul) & (df['Sınıf'].isin(secilen_siniflar))].drop_duplicates(subset=['Okul No'])
                        db_records_h  = []
                        for _, row in pool_students.iterrows():
                            o_no    = row['Okul No']
                            kontrol = df[(df['Okul'] == islem_okul) & (df['Okul No'] == o_no) &
                                         (df['Gorev_Adi'] == g_isim_h.strip()) & (df['Atanan_Ogretmen'] == h_ogrt)]
                            if kontrol.empty:
                                t_ders = (kb.get("brans","Genel") if h_ogrt == aktif_id
                                          else ayarlar["kullanicilar"].get(h_ogrt,{}).get("brans","Genel"))
                                db_records_h.append({
                                    'okul': islem_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': h_ogrt,
                                    'ders': t_ders, 'okul_no': o_no, 'ogrenci_adi_soyadi': row['Öğrenci Adı Soyadı'],
                                    'sinif': row['Sınıf'], 'gorev_turu': g_tur_h, 'gorev_adi': g_isim_h.strip(), 'dinamik_json': {}
                                })
                        if db_records_h:
                            supabase.table('gorevler').insert(db_records_h).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(db_records_h)} öğrenciye görev atandı!")
                            time.sleep(1); st.rerun()
                        else:
                            st.warning("Bu görev zaten atanmış. Mükerrer kayıt engellendi.")
            else:
                st.info("Bu okula ait öğrenci kaydı yok. Önce Excel ile yükleme yapın.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── HATASIZ: Geçmişi Düzenle (Sadece Silme ve Görüntüleme) ──
        elif aktif_ogr == "gecmis_duzenle":
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>✏️ Değerlendirilen Öğrencileri Görüntüle ve Sil</div>", unsafe_allow_html=True)
            st.info("💡 Öğrencilerin puanlarını/yorumlarını DÜZENLEMEK veya YAPAY ZEKA ÇALIŞTIRMAK için üst menüden '🤖 AI Değerlendirme' sekmesine geçiniz. Orada değerlendirilmiş öğrenciler yeşil tik ile görünür.")
            
            df_g = df_yetkili[df_yetkili['Gorev_Turu'] != "Karne Gorusu"]
            if df_g.empty:
                st.warning("Sisteme kayıtlı görev bulunmuyor.")
            else:
                c1, c2 = st.columns(2)
                secili_sinif = c1.selectbox("1️⃣ Sınıf Seçin", ["— Tüm Sınıflar —"] + sorted(df_g['Sınıf'].dropna().unique().tolist()))
                df_filt = df_g if secili_sinif == "— Tüm Sınıflar —" else df_g[df_g['Sınıf'] == secili_sinif]
                
                secili_gorev_isim = c2.selectbox("2️⃣ Görevi Seçin", ["— Seçiniz —"] + sorted(df_filt['Gorev_Adi'].dropna().unique().tolist()))
                if secili_gorev_isim != "— Seçiniz —":
                    df_secili = df_filt[df_filt['Gorev_Adi'] == secili_gorev_isim].copy()
                    
                    def durum_getir(row):
                        try: is_m = json.loads(str(row.get('Dinamik_JSON', '{}'))).get("muaf", False)
                        except: is_m = False
                        
                        # GÜVENLİ SAYI DÖNÜŞÜMÜ (HATA ÇÖZÜMÜ)
                        p_val = pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')
                        p = int(p_val) if pd.notna(p_val) else 0
                        
                        yorum = str(row.get('Genel Değerlendirme Yorumu', '')).strip()
                        
                        if is_m: return "🚫 Muaf"
                        elif p > 0 or yorum != "": return f"✅ {p} Puan"
                        else: return "⏳ Bekliyor"
                        
                    df_secili['Durum'] = df_secili.apply(durum_getir, axis=1)
                    st.dataframe(df_secili[['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Durum']], use_container_width=True, hide_index=True)
                    
                    st.markdown("#### 🗑️ Öğrenciyi Görevden Tamamen Sil")
                    sil_ogr = st.selectbox("Silinecek Öğrenci", ["— Seçiniz —"] + df_secili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist())
                    if sil_ogr != "— Seçiniz —" and st.button("🗑️ Görevden Sil", type="primary"):
                        o_no_sil = sil_ogr.split(" - ")[0].strip()
                        supabase.table('gorevler').delete().eq('okul_no', o_no_sil).eq('gorev_adi', secili_gorev_isim).execute()
                        st.cache_data.clear(); st.success("Silindi!"); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Silme İşlemleri ──
        elif aktif_ogr == "silme":
            st.markdown('<div class="warn-banner">⚠️ Silme işlemleri geri alınamaz! Silmeden önce <b>Raporlar → Veri Yedekleme</b> bölümünden yedek alın.</div>', unsafe_allow_html=True)
            render_nav_bar(ALT_MENU_SIL, "nav_sil_alt", is_main=False)
            aktif_sil = st.session_state.get("nav_sil_alt", "tekil_sil")

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if aktif_sil == "tekil_sil":
                st.markdown("<div class='section-header'>📌 Tekil Kayıt Sil</div>", unsafe_allow_html=True)
                if not df_yetkili.empty:
                    s_liste    = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                    silinecek  = st.selectbox("Silinecek Kayıt", ["— Seçiniz —"] + s_liste)
                    if st.button("🗑️ Bu Kaydı Sil", type="primary") and silinecek != "— Seçiniz —":
                        o_no = silinecek.split(" - ")[0].strip()
                        g_ad = silinecek.split(" | ")[1].strip()
                        supabase.table('gorevler').delete().eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                        st.cache_data.clear()
                        st.success("Silindi.")
                        time.sleep(1); st.rerun()
                else:
                    st.info("Silinecek kayıt yok.")

            elif aktif_sil == "sinif_sil":
                st.markdown("<div class='section-header'>🏫 Sınıf Toplu Sil</div>", unsafe_allow_html=True)
                sil_okul2 = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul", sorted(ayarlar["okullar"]), key="sil_okul2")
                mevcut_siniflar_sil = sorted(df[df['Okul'] == sil_okul2]['Sınıf'].dropna().unique().tolist()) if not df.empty else []
                if mevcut_siniflar_sil:
                    secilen_sinif_sil = st.multiselect("Silinecek Sınıflar", mevcut_siniflar_sil)
                    secilen_gorev_sil = st.selectbox("Sadece Bu Görev (Opsiyonel)",
                                                      ["Tüm Görevler"] + sorted(df[df['Okul'] == sil_okul2]['Gorev_Adi'].dropna().unique().tolist()))
                    if secilen_sinif_sil:
                        kac = len(df[(df['Okul'] == sil_okul2) & (df['Sınıf'].isin(secilen_sinif_sil))])
                        st.warning(f"Bu işlem {kac} kaydı silecek!")
                        onay = st.checkbox(f"Evet, {kac} kaydı silmek istiyorum.")
                        if onay and st.button("🗑️ Sınıf Verilerini Sil", type="primary"):
                            q = supabase.table('gorevler').delete().eq('okul', sil_okul2).in_('sinif', secilen_sinif_sil)
                            if secilen_gorev_sil != "Tüm Görevler":
                                q = supabase.table('gorevler').delete().eq('okul', sil_okul2).in_('sinif', secilen_sinif_sil).eq('gorev_adi', secilen_gorev_sil)
                            q.execute()
                            st.cache_data.clear()
                            st.success("Silindi.")
                            time.sleep(1); st.rerun()
                else:
                    st.info("Bu okulda sınıf verisi yok.")

            elif aktif_sil == "okul_sil":
                st.markdown("<div class='section-header'>🏢 Okul Toplu Sil</div>", unsafe_allow_html=True)
                if rol != "admin":
                    st.error("Bu işlem sadece yöneticiler tarafından yapılabilir.")
                else:
                    sil_okul3 = st.selectbox("Tüm Verileri Silinecek Okul", sorted(ayarlar["okullar"]), key="sil_okul3")
                    kac3 = len(df[df['Okul'] == sil_okul3]) if not df.empty else 0
                    if kac3 > 0:
                        st.error(f"⛔ Bu işlem {sil_okul3} okuluna ait TÜM {kac3} kaydı silecek!")
                        onay3 = st.checkbox(f"Evet, {sil_okul3} okulunun tüm {kac3} kaydını siliyorum.")
                        if onay3 and st.button("⛔ Okul Verilerini Komple Sil", type="primary"):
                            supabase.table('gorevler').delete().eq('okul', sil_okul3).execute()
                            st.cache_data.clear()
                            st.success("Silindi.")
                            time.sleep(1); st.rerun()
                    else:
                        st.info("Bu okulda kayıt yok.")
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: AI DEĞERLENDİRME VE GÜNCELLEME MERKEZİ (TAM KONTROL)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ai_degerlendirme":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🤖 Yapay Zeka Destekli Puanlama & Yeniden Değerlendirme</div>", unsafe_allow_html=True)

        if df_yetkili.empty:
            st.warning("Değerlendirilecek görev bulunamadı.")
        else:
            df_g = df_yetkili[df_yetkili['Gorev_Turu'] != "Karne Gorusu"].copy()
            if df_g.empty:
                st.warning("Sisteme kayıtlı görev (sınav/proje) bulunmuyor.")
            else:
                st.markdown("**🔍 Değerlendirilecek veya Güncellenecek Öğrenciyi Bul**")
                col_f1, col_f2 = st.columns(2)
                
                secili_sinif = col_f1.selectbox("1️⃣ Sınıf Seçin", ["— Tümü —"] + sorted(df_g['Sınıf'].dropna().unique().tolist()))
                if secili_sinif != "— Tümü —": df_g = df_g[df_g['Sınıf'] == secili_sinif]
                    
                secili_gorev_filtresi = col_f2.selectbox("2️⃣ Görev Seçin", ["— Tümü —"] + sorted(df_g['Gorev_Adi'].dropna().unique().tolist()))
                if secili_gorev_filtresi != "— Tümü —": df_g = df_g[df_g['Gorev_Adi'] == secili_gorev_filtresi]

                # --- YENİ VE GÜVENLİ: DURUM ANALİZİ ---
                def detayli_durum(row):
                    try: d_json = json.loads(str(row.get('Dinamik_JSON', '{}')))
                    except: d_json = {}
                    is_muaf = d_json.get("muaf", False)
                    
                    # GÜVENLİ SAYI DÖNÜŞÜMÜ
                    p_val = pd.to_numeric(row.get('Toplam Puan', 0), errors='coerce')
                    puan = int(p_val) if pd.notna(p_val) else 0
                    
                    yorum = str(row.get('Genel Değerlendirme Yorumu', '')).strip()
                    
                    if is_muaf: return 2, "🚫 Muaf"
                    elif puan > 0 or yorum != "": return 1, f"✅ Değerlendirildi ({puan} Puan)"
                    else: return 0, "⏳ Bekliyor"
                
                df_g[['Sira', 'Durum_Icon']] = df_g.apply(detayli_durum, axis=1, result_type="expand")
                df_g = df_g.sort_values(by=['Sira', 'Okul No']) # Bekleyenler (0) en üstte görünsün diye sıralıyoruz
                
                # --- YENİ EKLENEN KOD: Eğer veritabanında çift kayıt varsa sadece birini göster ---
                df_g = df_g.drop_duplicates(subset=['Okul No', 'Gorev_Adi'], keep='last')
                
                puan_liste = df_g.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']} | {r['Durum_Icon']}", axis=1).tolist()
                
                st.markdown("---")
                secili_gorev = st.selectbox("3️⃣ Öğrenciyi Seçin (Bekleyenler üsttedir, değerlendirilmişleri seçip güncelleyebilirsiniz)", ["— Seçiniz —"] + puan_liste)
                
                s_isimler = list(ayarlar.get("sablonlar", {}).keys())
                sec_sablon_ismi = st.selectbox("📋 Kullanılacak Şablon", s_isimler)
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
                        
                        dinamik_okunan = {}
                        try:
                            if pd.notna(bilgi.get('Dinamik_JSON', '')):
                                dinamik_okunan = json.loads(str(bilgi['Dinamik_JSON']))
                        except: pass
                        
                        is_muaf = dinamik_okunan.get("muaf", False)

                        # Form state yönetimi
                        if st.session_state.get("aktif_idx") != idx:
                            st.session_state["aktif_idx"] = idx
                            for k in aktif_sablon:
                                st.session_state[f"vp_{k['id']}"] = int(dinamik_okunan.get(f"{k['id']}_puan", 0))
                                st.session_state[f"va_{k['id']}"] = str(dinamik_okunan.get(f"{k['id']}_aciklama", ""))
                            st.session_state["vg"] = str(bilgi.get('Genel Değerlendirme Yorumu', ""))

                        st.markdown(f"""
                        <div style="background:#eff6ff;padding:14px;border-radius:10px;border-left:4px solid #3b82f6;margin-bottom:14px;">
                            <strong>{bilgi.get('Öğrenci Adı Soyadı','')}</strong> &nbsp;|&nbsp;
                            Sınıf: {bilgi.get('Sınıf','')} &nbsp;|&nbsp;
                            Görev: {bilgi.get('Gorev_Adi','')} &nbsp;|&nbsp; No: {bilgi.get('Okul No','')}
                        </div>""", unsafe_allow_html=True)

                        # --- MUAFİYET VE SIFIRLAMA BUTONLARI ---
                        c_m1, c_m2 = st.columns(2)
                        
                        # GÜVENLİ ID VE PUAN (Hata Veren Yerin Kesin Çözümü)
                        mevcut_puan_ham = pd.to_numeric(bilgi.get('Toplam Puan', 0), errors='coerce')
                        mevcut_puan_int = int(mevcut_puan_ham) if pd.notna(mevcut_puan_ham) else 0

                        if is_muaf:
                            st.error("🚫 Bu öğrenci bu projeden MUAF tutulmuştur. Raporlarda görünmez ve ortalamaya katılmaz.")
                            if c_m1.button("🔄 Muafiyeti Kaldır (Öğrenciyi Yeniden Değerlendir)", use_container_width=True):
                                dinamik_okunan["muaf"] = False
                                supabase.table('gorevler').update({'dinamik_json': dinamik_okunan, 'toplam_puan': 0, 'genel_degerlendirme_yorumu': ""}).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                                st.cache_data.clear(); st.rerun()
                        else:
                            if c_m1.button("🚫 Bu Öğrenciyi Projeden Muaf Tut", use_container_width=True):
                                dinamik_okunan["muaf"] = True
                                supabase.table('gorevler').update({'dinamik_json': dinamik_okunan, 'toplam_puan': 0, 'genel_degerlendirme_yorumu': "Projeyi almadı."}).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                                st.cache_data.clear(); st.rerun()
                                
                            if mevcut_puan_int > 0 or str(bilgi.get('Genel Değerlendirme Yorumu', '')).strip() != "":
                                if c_m2.button("🔄 Değerlendirmeyi Sıfırla (Başa Dön)", use_container_width=True):
                                    for k in aktif_sablon:
                                        dinamik_okunan[f"{k['id']}_puan"] = 0
                                        dinamik_okunan[f"{k['id']}_aciklama"] = ""
                                    supabase.table('gorevler').update({'dinamik_json': dinamik_okunan, 'toplam_puan': 0, 'genel_degerlendirme_yorumu': ""}).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                                    st.cache_data.clear(); st.rerun()

                        # --- YAPAY ZEKA VE PUANLAMA FORMU ---
                        if not is_muaf:
                            st.markdown("**🤖 AI Modu Seçin:**")
                            ai_modu = st.radio("AI Modu", ["A", "B", "C"], format_func=lambda x: {"A": "📝 Mod A — Yorumdan Puan Üret", "B": "🎯 Mod B — Hedef Puandan Dağıt", "C": "✋ Mod C — Manuel Puanı Açıkla"}[x], horizontal=True, label_visibility="collapsed")
                            
                            st.markdown("**📚 Görevin Konusu / Değerlendirme Notlarınız (Tüm modlar için)**")
                            ham_metin = st.text_area("Hangi konu işlendi, nelerde eksiklik var veya neye göre değerlendirilecek?", placeholder="Örn: Açılar ve çokgenler projesi. Geometrik çizimleri çok iyi ama formüllerde ufak hatalar yapmış...", label_visibility="collapsed")
                            
                            hedef_puan = 85
                            mod_c_puanlari = {}
                            
                            if ai_modu == "B":
                                hedef_puan = st.slider("Hedef Puan Belirleyin", 0, 100, 85)
                            elif ai_modu == "C":
                                st.info("👇 Lütfen yapay zekanın pedagojik açıklama yazmasını istediğiniz puanları buraya girin:")
                                sutunlar = st.columns(len(aktif_sablon))
                                for i, k in enumerate(aktif_sablon):
                                    mod_c_puanlari[k['id']] = sutunlar[i % len(sutunlar)].number_input(f"{k['baslik'][:15]}...", 0, k['max'], int(st.session_state.get(f"vp_{k['id']}", k['max'])), key=f"tmp_{k['id']}")

                            if st.button("✨ Yapay Zekayı Çalıştır", use_container_width=True):
                                with st.spinner("Yapay zeka isme özel analiz ediyor..."):
                                    try:
                                        # DÜZELTME: Mod C ise form dışındaki yeni kutulardan oku, değilse eski usul devam et
                                        m_p_d = mod_c_puanlari if ai_modu == "C" else {k['id']: st.session_state.get(f"vp_{k['id']}", 0) for k in aktif_sablon}
                                        
                                        res   = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, m_p_d, kb.get("ad",""), bilgi['Ders'])
                                        
                                        ai_toplam = 0 
                                        for k in aktif_sablon:
                                            if k['id'] in res.get("puanlar", {}): 
                                                gelen_puan = int(res["puanlar"][k['id']])
                                                st.session_state[f"vp_{k['id']}"] = gelen_puan
                                                ai_toplam += gelen_puan 
                                                
                                            if k['id'] in res.get("aciklamalar", {}): 
                                                st.session_state[f"va_{k['id']}"] = res["aciklamalar"][k['id']]
                                                
                                        if "genel" in res: st.session_state["vg"] = res["genel"]
                                        
                                        # Sistemi yeniliyoruz ki aşağıdaki asıl puanlama formu anında dolsun
                                        st.session_state["ai_basari_mesaji"] = f"✅ Değerlendirme hazır! 🎯 İşlenen Toplam Puan: **{ai_toplam} / 100**"
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"AI hatası: {e}")
                                        
                            # YENİ KOD: Sayfa yenilendikten sonra başarı mesajını formun hemen üstünde göstermek için
                            if "ai_basari_mesaji" in st.session_state:
                                st.success(st.session_state["ai_basari_mesaji"])
                                del st.session_state["ai_basari_mesaji"] # Gösterdikten sonra siliyoruz

                            st.markdown("#### 📝 Puanlama Formu")
                            with st.form("kayit_formu"):
                                toplam_h = 0
                                for k in aktif_sablon:
                                    cc1, cc2 = st.columns([1, 3])
                                    pv = cc1.number_input(f"📌 {k['baslik']} (Max: {k['max']})", 0, k['max'], key=f"vp_{k['id']}")
                                    av = cc2.text_area("Açıklama", key=f"va_{k['id']}", height=68)
                                    toplam_h += pv
                                gv = st.text_area("💬 Genel Yorum", key="vg", height=90)
                                st.info(f"Toplam Puan: {toplam_h} / 100")
                                
                                if st.form_submit_button("💾 Veritabanına Kaydet", use_container_width=True):
                                    dinamik_okunan["muaf"] = False
                                    for k in aktif_sablon:
                                        dinamik_okunan[f"{k['id']}_puan"] = st.session_state[f"vp_{k['id']}"]
                                        dinamik_okunan[f"{k['id']}_aciklama"] = st.session_state[f"va_{k['id']}"]
                                    supabase.table('gorevler').update({
                                        'dinamik_json': dinamik_okunan, 'genel_degerlendirme_yorumu': gv, 'toplam_puan': toplam_h
                                    }).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                                    st.cache_data.clear()
                                    st.success("✅ Kalıcı olarak kaydedildi!")
                                    time.sleep(1); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: RAPORLAR
    # ══════════════════════════════════════════════════
    elif aktif_ana == "raporlar":
        render_nav_bar(ALT_MENU_RAPORLAR, "nav_rapor_alt", is_main=False)
        aktif_rapor = st.session_state.get("nav_rapor_alt", "sinif_rapor")

        if aktif_rapor == "sinif_rapor":
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>📊 Sınıf Raporları ve Analizler</div>", unsafe_allow_html=True)
            
            if not df_yetkili.empty:
                df_r_yetkili = df_yetkili[df_yetkili['Gorev_Turu'] != "Karne Gorusu"].copy()
                
                # --- YENİ: "Projeyi Almadı (Muaf)" İşaretli Öğrencileri Raporlardan Çıkar ---
                def muaf_mi_kontrol(json_str):
                    try: return json.loads(str(json_str)).get("muaf", False)
                    except: return False
                
                df_r_yetkili = df_r_yetkili[~df_r_yetkili['Dinamik_JSON'].apply(muaf_mi_kontrol)]
                
                c_r1, c_r2 = st.columns([1, 1])
                r_sinif = c_r1.selectbox("Sınıf Seçin", ["Tümü"] + sorted(df_r_yetkili['Sınıf'].dropna().unique()))
                df_r = df_r_yetkili if r_sinif == "Tümü" else df_r_yetkili[df_r_yetkili['Sınıf'] == r_sinif]
                
                g_filtre = c_r2.selectbox("Görev Filtrele", ["Tümü"] + sorted(df_r['Gorev_Adi'].dropna().unique().tolist()))
                if g_filtre != "Tümü":
                    df_r = df_r[df_r['Gorev_Adi'] == g_filtre]

                if not df_r.empty:
                    # --- YENİ EKLENEN KOD: Raporlarda ve çıktılarda çift isimleri teke düşür ---
                    df_r = df_r.drop_duplicates(subset=['Okul No', 'Gorev_Adi'], keep='last')
                    
                    df_r_copy = df_r.copy()
                    df_r_copy['Toplam Puan'] = pd.to_numeric(df_r_copy['Toplam Puan'], errors='coerce').fillna(0)
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    col_s1.markdown(f'<div class="stat-card"><div class="stat-number">{len(df_r_copy)}</div><div class="stat-label">Toplam Kayıt</div></div>', unsafe_allow_html=True)
                    col_s2.markdown(f'<div class="stat-card green"><div class="stat-number">{round(df_r_copy["Toplam Puan"].mean(),1)}</div><div class="stat-label">Ortalama</div></div>', unsafe_allow_html=True)
                    col_s3.markdown(f'<div class="stat-card orange"><div class="stat-number">{int(df_r_copy["Toplam Puan"].max())}</div><div class="stat-label">En Yüksek</div></div>', unsafe_allow_html=True)
                    col_s4.markdown(f'<div class="stat-card red"><div class="stat-number">{len(df_r_copy[df_r_copy["Toplam Puan"]==0])}</div><div class="stat-label">Değerlendirilmemiş</div></div>', unsafe_allow_html=True)

                    st.dataframe(
                        df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Turu','Gorev_Adi','Toplam Puan']].sort_values('Toplam Puan', ascending=False),
                        use_container_width=True, hide_index=True
                    )

                    # Eski 3 sütunluk yapı yerine 4 sütunluk yapı
                    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
                    
                    # 1. Excel Çizelgesi
                    out_xls = io.BytesIO()
                    with pd.ExcelWriter(out_xls, engine='xlsxwriter') as writer:
                        df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Turu','Gorev_Adi','Toplam Puan']].to_excel(writer, index=False, sheet_name='Cizelge')
                    c_btn1.download_button("📊 Excel Çizelgesi", data=out_xls.getvalue(),
                                           file_name=f"{r_sinif}_Cizelge.xlsx", use_container_width=True)

                    # 2. Kişisel Karneler
                    if c_btn2.button("🖨️ Kişisel Karneler (HTML)", use_container_width=True):
                        s_aktif = ayarlar["sablonlar"].get(list(ayarlar["sablonlar"].keys())[0], CEKIRDEK_SABLON)
                        h_cikti = toplu_karne_html_dosyasi_uret(df_r, kb.get("ad",""), kb.get("brans",""), s_aktif)
                        st.download_button("📥 HTML Karneleri İndir", data=h_cikti,
                                           file_name=f"{r_sinif}_Karneler.html", mime="text/html", use_container_width=True)

                    # 3. Sınıf Analiz Raporu
                    if c_btn3.button("📈 Sınıf Analiz Raporu", use_container_width=True):
                        analiz_html = sinif_analiz_raporu(df_r, r_sinif, kb.get("ad",""))
                        st.download_button("📥 Analiz Raporunu İndir", data=analiz_html,
                                           file_name=f"{r_sinif}_Analiz.html", mime="text/html", use_container_width=True)

                    # 4. YENİ EKLENEN: İDARE RAPORU (ÇAPRAZ TABLO)
                    if c_btn4.button("📋 İdare Raporu (Toplu Liste)", type="primary", use_container_width=True):
                        # Gerekli parametreleri hazırlayıp gönderiyoruz
                        s_aktif = ayarlar["sablonlar"].get(list(ayarlar["sablonlar"].keys())[0], CEKIRDEK_SABLON)
                        # df_r içindeki ilk satırdan görev adını alıyoruz
                        g_adi_aktif = df_r.iloc[0]['Gorev_Adi'] if not df_r.empty else "Proje" 
                        idare_html = toplu_kriterli_liste_html(df_r, r_sinif, kb.get("brans",""), kb.get("ad",""), s_aktif, g_adi_aktif)
                        st.download_button("📥 İdare Raporunu İndir", data=idare_html,
                                           file_name=f"{r_sinif}_Idare_Liste_Raporu.html", mime="text/html", use_container_width=True)
                else:
                    st.info("Rapor oluşturmak için veri bulunamadı.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif aktif_rapor == "yedekleme":
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>💾 Veri Yedekleme</div>", unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)

   # ══════════════════════════════════════════════════
    # SEKME: E-OKUL KARNE (Gelişmiş Yapay Zeka, Kalıcı Liste ve Excel Arşivi)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "eokul":
                
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📝 E-Okul Karne Görüşü & Kalıcı Sınıf Listesi Yönetimi</div>", unsafe_allow_html=True)
        st.info("💡 Liste bir kez yüklenir ve sistemde kalır. Hibrit AI (Groq + Gemini) sayesinde sistem tıkanmadan saniyeler içinde tüm sınıfa karne üretebilirsiniz.")
        
        # --- API ANAHTARLARINI GİZLİ KASADAN (SECRETS) ÇEKME ---
        try:
            GROQ_KEYS = st.secrets["GROQ_API_KEYS"]
            GEMINI_KEYS = st.secrets["GEMINI_API_KEYS"]
        except Exception as e:
            st.error("⚠️ HATA: API Anahtarları Streamlit gizli kasasında (secrets.toml) bulunamadı. Lütfen ayarlarınızı kontrol edin.")
            st.stop()

        def call_ai_with_fallback(prompt):
            # Önce GROQ dener (Çok daha hızlıdır ve kota sorunu yoktur)
            for _ in range(2):
                try:
                    g_key = random.choice(GROQ_KEYS)
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {g_key}", "Content-Type": "application/json"}
                    payload = {"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
                    r = requests.post(url, headers=headers, json=payload, timeout=10)
                    r.raise_for_status()
                    return r.json()["choices"][0]["message"]["content"].strip()
                except:
                    continue
            
            # Groq başarısız olursa GEMINI dener
            for _ in range(2):
                try:
                    gm_key = random.choice(GEMINI_KEYS)
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gm_key}"
                    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
                    r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=10)
                    r.raise_for_status()
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                except:
                    continue
                    
            return "API Hatası: Sistem şu an aşırı yoğun. Lütfen 1 dakika sonra tekrar deneyin."

        def dogal_karne_yazdir(isim, sinif, ders_notlari_metni, davranis, ogretmen_tuyosu, ogrt_isim):
            davranis_mesaji = "Davranış notu düşük, bunu nazik ve pedagojik bir uyarıyla dile getir." if int(davranis) < 60 else "Davranışları çok iyi, bunu mutlaka öv."
            prompt = f"""Sen tecrübeli ve şefkatli bir öğretmensin. Adın {ogrt_isim}. {sinif} sınıfından öğrencin '{isim}' için e-okul sistemine girilecek bir dönem sonu karne görüşü yazıyorsun.
Öğrencinin Ders Notları:
{ders_notlari_metni}
Davranış Puanı (100 üzerinden): {davranis}
Sisteme tuttuğum not (Bunu yoruma doğalca yedir): "{ogretmen_tuyosu}"

LÜTFEN ŞUNLARA DİKKAT ET:
1. Son derece doğal ve insani bir dil kullan. Çocuğu yıllardır tanıyormuşsun gibi hissettir.
2. Doğrudan 'Sevgili {isim},' diye başla. Soyadını kullanma.
3. {davranis_mesaji}
4. Toplam 3-4 cümleyi geçmesin.
Karne Görüşü:"""
            return call_ai_with_fallback(prompt)

        # --- YIL VE DÖNEM DİNAMİĞİ ---
        yillar = []
        for y in range(2015, 2035):
            yillar.append(f"{y}-{y+1} Eğitim Yılı - 1. Dönem")
            yillar.append(f"{y}-{y+1} Eğitim Yılı - 2. Dönem")
        
        varsayilan_index = yillar.index("2025-2026 Eğitim Yılı - 2. Dönem") if "2025-2026 Eğitim Yılı - 2. Dönem" in yillar else 0
        
        c_donem, c_bos = st.columns([1, 2])
        secili_donem = c_donem.selectbox("📚 İşlem Yapılacak Dönemi Seçin", yillar, index=varsayilan_index)

        df_karne = df_yetkili[(df_yetkili['Gorev_Turu'] == 'Karne Gorusu') & (df_yetkili['Gorev_Adi'] == secili_donem)].copy()
        
        tab_aktif, tab_arsiv = st.tabs(["📋 Karne Listesi ve Görüş Yazma", "📥 Excel Çıktısı Al ve Arşive Gözat"])

        with tab_aktif:
            if df_karne.empty:
                st.markdown(f"**📌 {secili_donem} için henüz liste yüklenmemiş. Lütfen aşağıdan Excel dosyanızı yükleyin.**")
                col_dl, col_up = st.columns([1, 2])
                col_dl.download_button("📄 Örnek E-Okul Excel Şablonu İndir", data=eokul_sablon_olustur(), file_name="Eokul_Sablon.xlsx", use_container_width=True)
                k_dosya = col_up.file_uploader("E-Okul Not Listesini Yükle (Excel/CSV)", type=['xlsx','csv','xls'])
                
                if k_dosya:
                    yukleme_tercihi = st.radio("Yükleme Seçeneği", [
                        "➕ Eski listeyi KORU, sadece yeni öğrencileri ekle", 
                        "🗑️ Eski listeyi SİL ve sadece bu dosyayı yükle"
                    ], horizontal=True)
                    
                    if st.button("💾 Listeyi Veritabanına Kaydet", type="primary", use_container_width=True):
                        with st.spinner("Liste analiz ediliyor ve kaydediliyor..."):
                            kdf = pd.read_csv(k_dosya, sep=None, engine='python') if k_dosya.name.endswith('.csv') else pd.read_excel(k_dosya)
                            kdf = kdf.fillna("") 
                            cols = kdf.columns.tolist()
                            
                            no_col = next((c for c in cols if "no" in str(c).lower()), cols[0])
                            ad_col = next((c for c in cols if "ad" in str(c).lower()), cols[1] if len(cols)>1 else cols[0])
                            sinif_col = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols)>2 else None)
                            davranis_col = next((c for c in cols if "davran" in str(c).lower()), None)
                            not_cols = [c for c in cols if c not in [no_col, ad_col, sinif_col, davranis_col]]

                            if "SİL" in yukleme_tercihi and not df_karne.empty:
                                supabase.table('gorevler').delete().eq('atanan_ogretmen', aktif_id).eq('gorev_turu', 'Karne Gorusu').eq('gorev_adi', secili_donem).execute()

                            yeni_kayitlar = []
                            for i, row in kdf.iterrows():
                                o_no = str(row[no_col]).strip().replace('.0', '')
                                if not o_no or o_no.lower() == "nan": continue
                                
                                dav_val = 100
                                if davranis_col and str(row[davranis_col]).strip() != "":
                                    try: dav_val = int(float(str(row[davranis_col]).replace(",", ".")))
                                    except: pass

                                notlar_dict = {d: str(row[d]) for d in not_cols if str(row[d]).strip() != ""}
                                dinamik_veri = {"notlar": notlar_dict, "davranis": dav_val, "ogretmen_notu": "", "durum": "Bekliyor ⏳"}
                                
                                var_mi = not df_karne[df_karne['Okul No'] == o_no].empty if not df_karne.empty else False
                                if not var_mi or "SİL" in yukleme_tercihi:
                                    yeni_kayitlar.append({
                                        'okul': kb.get("okul"), 'ekleyen': aktif_id, 'atanan_ogretmen': aktif_id,
                                        'ders': "Davranış / Karne", 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col],
                                        'sinif': str(row[sinif_col]) if sinif_col else "Bilinmiyor", 
                                        'gorev_turu': 'Karne Gorusu', 'gorev_adi': secili_donem, 
                                        'dinamik_json': dinamik_veri, 'genel_degerlendirme_yorumu': ""
                                    })
                            
                            if yeni_kayitlar:
                                supabase.table('gorevler').insert(yeni_kayitlar).execute()
                                st.cache_data.clear()
                                st.rerun()
            
            else:
                st.success(f"✅ {secili_donem} dönemi aktif. Toplam {len(df_karne)} öğrenciniz bulunuyor.")
                
                # --- ÜST BUTONLAR ---
                col_b1, col_b2, col_b3 = st.columns(3)
                
                if col_b1.button("🤖 Sınıftaki TÜM ÖĞRENCİLERE Yapay Zeka Karne Üret", type="primary", use_container_width=True):
                    bar = st.progress(0)
                    satirlar = df_karne.to_dict('records')
                    
                    st.info("⏳ Hibrit motor devrede. İşlem bitene kadar sayfayı kapatmayın...")
                    
                    for i, r in enumerate(satirlar):
                        d_json = json.loads(str(r['Dinamik_JSON'])) if isinstance(r['Dinamik_JSON'], str) else r['Dinamik_JSON']
                        
                        anlik_davranis = st.session_state.get(f"dav_{r['id']}", d_json.get('davranis', 100))
                        anlik_tuyo = st.session_state.get(f"tuyo_{r['id']}", d_json.get('ogretmen_notu', ''))
                        
                        n_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in d_json.get('notlar', {}).items() if str(notu).strip() != ""])
                        
                        yeni_gorus = dogal_karne_yazdir(r['Öğrenci Adı Soyadı'], r['Sınıf'], n_metni, anlik_davranis, anlik_tuyo, kb["ad"])
                        
                        d_json['davranis'] = anlik_davranis
                        d_json['ogretmen_notu'] = anlik_tuyo
                        st.session_state[f"gorus_{r['id']}"] = yeni_gorus
                        
                        supabase.table('gorevler').update({
                            'genel_degerlendirme_yorumu': yeni_gorus,
                            'dinamik_json': d_json
                        }).eq('id', r['id']).execute()
                        
                        bar.progress((i + 1) / len(satirlar))
                        time.sleep(1.5) # Güvenli bekleme süresi
                        
                    st.cache_data.clear()
                    st.success("✅ Tüm sınıf için karne görüşleri başarıyla üretildi!")
                    time.sleep(1)
                    st.rerun()

                if col_b2.button("💾 Tüm Değişiklikleri Veritabanına Kaydet", use_container_width=True):
                    with st.spinner("Kaydediliyor..."):
                        for _, r in df_karne.iterrows():
                            d_json = json.loads(str(r['Dinamik_JSON'])) if isinstance(r['Dinamik_JSON'], str) else r['Dinamik_JSON']
                            
                            anlik_dav = st.session_state.get(f"dav_{r['id']}", d_json.get('davranis', 100))
                            anlik_tuyo = st.session_state.get(f"tuyo_{r['id']}", d_json.get('ogretmen_notu', ''))
                            anlik_gorus = st.session_state.get(f"gorus_{r['id']}", str(r.get('Genel Değerlendirme Yorumu', '')))
                            
                            d_json['davranis'] = anlik_dav
                            d_json['ogretmen_notu'] = anlik_tuyo
                                
                            supabase.table('gorevler').update({
                                'genel_degerlendirme_yorumu': anlik_gorus,
                                'dinamik_json': d_json
                            }).eq('id', r['id']).execute()
                            
                        st.cache_data.clear()
                        st.success("Tüm öğrencilerin verileri başarıyla kaydedildi!")
                        time.sleep(1)
                        st.rerun()

                if col_b3.button("🗑️ Bu Dönemin Listesini Tamamen Sil", use_container_width=True):
                    supabase.table('gorevler').delete().eq('atanan_ogretmen', aktif_id).eq('gorev_turu', 'Karne Gorusu').eq('gorev_adi', secili_donem).execute()
                    st.cache_data.clear()
                    st.rerun()

                st.markdown("---")
                
                # --- ÖĞRENCİ LİSTESİ ---
                for idx, row in df_karne.iterrows():
                    d_json = json.loads(str(row['Dinamik_JSON'])) if isinstance(row['Dinamik_JSON'], str) else row['Dinamik_JSON']
                    
                    mevcut_gorus = str(row.get('Genel Değerlendirme Yorumu', ''))
                    durum_ikon = "✅ Yazıldı" if mevcut_gorus.strip() else "⏳ Bekliyor"
                    
                    with st.expander(f"🎓 {row['Okul No']} - {row['Öğrenci Adı Soyadı']} | {durum_ikon}", expanded=False):
                        c_not, c_girdi, c_ai = st.columns([1, 1, 2])
                        
                        with c_not:
                            st.markdown("**📊 Ders Notları**")
                            notlar_dict = d_json.get('notlar', {})
                            if notlar_dict:
                                for k, v in notlar_dict.items():
                                    st.markdown(f"<div style='font-size:0.85rem; padding:2px 0;'><b>{k}:</b> <span style='color:#2563eb; font-weight:bold;'>{v}</span></div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='font-size:0.85rem;'>Not bulunamadı.</span>", unsafe_allow_html=True)
                                
                        with c_girdi:
                            st.markdown("**✍️ Öğretmen Dokunuşu**")
                            dav_val = st.number_input("Davranış Notu", min_value=0, max_value=100, value=int(d_json.get('davranis', 100)), key=f"dav_{row['id']}")
                            tuyo_val = st.text_area("Yapay Zekaya Özel Not", value=d_json.get('ogretmen_notu', ''), height=85, key=f"tuyo_{row['id']}", placeholder="Örn: Sınıfta çok aktif...")
                            
                            if st.button("✨ Sadece Buna AI Üret", key=f"ai_btn_{row['id']}", use_container_width=True):
                                with st.spinner("Yorum yazılıyor..."):
                                    n_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_dict.items() if str(notu).strip() != ""])
                                    yeni_gorus = dogal_karne_yazdir(row['Öğrenci Adı Soyadı'], row['Sınıf'], n_metni, dav_val, tuyo_val, kb["ad"])
                                    
                                    d_json['davranis'] = dav_val
                                    d_json['ogretmen_notu'] = tuyo_val
                                    st.session_state[f"gorus_{row['id']}"] = yeni_gorus
                                    
                                    supabase.table('gorevler').update({
                                        'genel_degerlendirme_yorumu': yeni_gorus,
                                        'dinamik_json': d_json
                                    }).eq('id', row['id']).execute()
                                    
                                    st.cache_data.clear()
                                    st.rerun()

                        with c_ai:
                            st.markdown("**🤖 Karne Görüşü (Önizleme & Düzenleme)**")
                            st.text_area("Karne Görüşü", value=st.session_state.get(f"gorus_{row['id']}", mevcut_gorus), height=170, key=f"gorus_{row['id']}", label_visibility="collapsed")

        # ---------------------------------------------------------
        # SEKME 2: YILLARA GÖRE POP-UP KARNE ARŞİVİ VE YÖNETİMİ
        # ---------------------------------------------------------
        with tab_arsiv:
            st.markdown("#### 🗂️ Yıllara / Dönemlere Göre Karne Görüşü Arşivi")
            st.info("Arşiv verileri her zaman günceldir. Buradan geçmiş yıllara ait listeleri indirebilir, yanlış yazılan öğrencileri pop-up menüden anında güncelleyip silebilirsiniz.")
            
            # Veritabanındaki tüm karne verilerini çek (Canlı ve her zaman güncel)
            df_tum_karneler = df_yetkili[df_yetkili['Gorev_Turu'] == 'Karne Gorusu'].copy()
            
            if df_tum_karneler.empty:
                st.warning("Sistemde arşivlenmiş herhangi bir karne verisi bulunamadı.")
            else:
                donemler = sorted(df_tum_karneler['Gorev_Adi'].dropna().unique(), reverse=True)
                
                for donem in donemler:
                    # Yıllara göre klasör mantığı (Açılır kapanır pencere)
                    with st.expander(f"📂 {donem} Arşivi", expanded=False):
                        df_donem = df_tum_karneler[df_tum_karneler['Gorev_Adi'] == donem].sort_values(by="Okul No")
                        
                        # --- EXCEL ÇIKTISI (ARŞİV İNDİRME) ---
                        export_data = [{"Okul No": r['Okul No'], "Ad Soyad": r['Öğrenci Adı Soyadı'], "Sınıf": r['Sınıf'], "Karne Görüşü": r.get('Genel Değerlendirme Yorumu', '')} for _, r in df_donem.iterrows()]
                        df_export = pd.DataFrame(export_data)
                        out_xls = io.BytesIO()
                        with pd.ExcelWriter(out_xls, engine='xlsxwriter') as w: 
                            df_export.to_excel(w, index=False, sheet_name='Arsiv')
                            w.sheets['Arsiv'].set_column('B:B', 25)
                            w.sheets['Arsiv'].set_column('D:D', 80)
                        st.download_button(f"📥 {donem} Excel Arşivini İndir", data=out_xls.getvalue(), file_name=f"Arsiv_{donem}.xlsx", type="primary", key=f"dl_{donem}")
                        
                        st.markdown("##### 👩‍🎓 Öğrenci Yönetimi")
                        
                        for idx, row in df_donem.iterrows():
                            # Pop-up (Popover) mantığı ile öğrenci bilgileri alt alta listelenir
                            col_isim, col_buton = st.columns([3, 1])
                            col_isim.markdown(f"**{row['Okul No']}** - {row['Öğrenci Adı Soyadı']} ({row['Sınıf']})")
                            
                            with col_buton:
                                # Popover: Tıklanınca açılan minik pencere (Ekranı aşağı kaydırmaz, karmaşa yaratmaz)
                                with st.popover("⚙️ Düzenle / Sil", use_container_width=True):
                                    st.markdown(f"**{row['Öğrenci Adı Soyadı']}** için işlem yapıyorsunuz.")
                                    
                                    # Canlı Güncelleme
                                    yeni_gorus = st.text_area("Görüşü Düzenle", value=row.get('Genel Değerlendirme Yorumu', ''), height=100, key=f"arsiv_gorus_{row['id']}")
                                    
                                    if st.button("💾 Kaydet", key=f"arsiv_kaydet_{row['id']}", use_container_width=True):
                                        supabase.table('gorevler').update({'genel_degerlendirme_yorumu': yeni_gorus}).eq('id', row['id']).execute()
                                        st.cache_data.clear()
                                        st.success("✅ Arşiv güncellendi!")
                                        time.sleep(1)
                                        st.rerun()
                                        
                                    st.markdown("---")
                                    # Silme
                                    if st.button("🗑️ Öğrenciyi Arşivden Sil", key=f"arsiv_sil_{row['id']}", type="primary", use_container_width=True):
                                        supabase.table('gorevler').delete().eq('id', row['id']).execute()
                                        st.cache_data.clear()
                                        st.success("🗑️ Kayıt silindi!")
                                        time.sleep(1)
                                        st.rerun()
# ══════════════════════════════════════════════════
    # SEKME: SÜPER YÖNETİCİ (ÖĞRETMEN VE OKUL YÖNETİMİ)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ogretmen_yonetim" and rol == "admin" and not admin_bakis:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<div class='section-header'>👑 Süper Yönetici Kontrol Merkezi</div>", unsafe_allow_html=True)
        st.info("💡 Buradan tüm öğretmenlerin şifre/okul bilgilerini düzenleyebilir, onay/engel durumlarını yönetebilir ve tek tıkla onların paneline sızarak (Gözat) yetkili işlem yapabilirsiniz. Ayrıca hatalı açılan mükerrer okulları birleştirebilirsiniz.")

        tab_ogrt, tab_okul = st.tabs(["👨‍🏫 Öğretmen Hesapları & Erişim", "🏢 Okul Hiyerarşisi & Birleştirme"])

        # --- SEKME 1: ÖĞRETMEN YÖNETİMİ ---
        with tab_ogrt:
            # Bekleyen Onayları Üste Çıkar
            bekleyenler = {k: v for k, v in ayarlar["kullanicilar"].items() if v.get("rol") != "admin" and not v.get("onayli", True)}
            if bekleyenler:
                st.markdown("#### ⏳ Onay Bekleyen Öğretmenler")
                for kadi, user in bekleyenler.items():
                    col_b1, col_b2, col_b3 = st.columns([3, 1, 1])
                    col_b1.warning(f"**{user['ad']}** | {user.get('okul','')} | {user.get('brans','')}")
                    if col_b2.button("✅ Onayla", key=f"onay_{kadi}", use_container_width=True):
                        ayarlar["kullanicilar"][kadi]["onayli"] = True
                        ayar_kaydet(ayarlar)
                        st.success("Öğretmen onaylandı!")
                        time.sleep(1); st.rerun()
                    if col_b3.button("❌ Reddet", key=f"reddet_{kadi}", type="primary", use_container_width=True):
                        del ayarlar["kullanicilar"][kadi]
                        ayar_kaydet(ayarlar)
                        st.error("Kayıt silindi.")
                        time.sleep(1); st.rerun()
                st.markdown("---")

            # Mevcut Öğretmenleri Listele (Okula Göre Filtreleme)
            st.markdown("#### 📋 Sistemdeki Öğretmenler")
            filtre_okul = st.selectbox("Okula Göre Filtrele", ["— Tüm Okullar —"] + sorted(ayarlar["okullar"]))
            
            for kadi, user in ayarlar["kullanicilar"].items():
                if user.get("rol") == "admin": continue
                if filtre_okul != "— Tüm Okullar —" and user.get("okul") != filtre_okul: continue
                
                aktif_mi = user.get("onayli", True)
                durum_renk = "success" if aktif_mi else "error"
                durum_metin = "Aktif" if aktif_mi else "Engellendi"
                
                with st.expander(f"👤 {user['ad']} ({user.get('okul', 'Okul Belirtilmemiş')}) | Durum: {durum_metin}"):
                    c_detay1, c_detay2 = st.columns([1, 1])
                    
                    with c_detay1:
                        st.markdown(f"**Kullanıcı Adı:** {kadi}")
                        st.markdown(f"**E-Posta:** {user.get('eposta', 'Belirtilmemiş')}")
                        st.markdown(f"**Branş:** {user.get('brans', '')}")
                        
                        # GÖZATMA (İMPERSONATION) ÖZELLİĞİ
                        st.markdown("---")
                        if st.button("👁️ Bu Öğretmenin Hesabına Gir (Gözat)", key=f"gozat_{kadi}", use_container_width=True):
                            st.session_state["admin_bakis_modu"] = True
                            st.session_state["admin_bakis_ogretmen"] = kadi
                            st.rerun()
                            
                    with c_detay2:
                        # BİLGİ DÜZENLEME FORMU
                        with st.form(f"duzenle_{kadi}"):
                            st.markdown("**✏️ Bilgileri Düzenle**")
                            y_ad = st.text_input("Ad Soyad", value=user['ad'])
                            y_okul = st.selectbox("Okul", sorted(ayarlar["okullar"]), index=sorted(ayarlar["okullar"]).index(user['okul']) if user['okul'] in ayarlar["okullar"] else 0)
                            y_brans = st.text_input("Branş", value=user.get('brans', ''))
                            y_sifre = st.text_input("Şifreyi Değiştir (Görünür)", value=user['sifre'])
                            
                            islem_btn, iptal_btn = st.columns(2)
                            if islem_btn.form_submit_button("💾 Güncelle"):
                                ayarlar["kullanicilar"][kadi].update({"ad": y_ad, "okul": y_okul, "brans": y_brans, "sifre": y_sifre})
                                ayar_kaydet(ayarlar)
                                st.success("Bilgiler güncellendi!")
                                time.sleep(1); st.rerun()

                        # ERİŞİM KONTROLÜ
                        if aktif_mi:
                            if st.button("🚫 Hesabı Engelle (Askıya Al)", key=f"engel_{kadi}", type="primary", use_container_width=True):
                                ayarlar["kullanicilar"][kadi]["onayli"] = False
                                ayar_kaydet(ayarlar)
                                st.rerun()
                        else:
                            if st.button("✅ Engeli Kaldır", key=f"kaldir_{kadi}", use_container_width=True):
                                ayarlar["kullanicilar"][kadi]["onayli"] = True
                                ayar_kaydet(ayarlar)
                                st.rerun()
                                
                        if st.button("🗑️ Öğretmeni Sistemden Tamamen Sil", key=f"sil_ogrt_{kadi}", use_container_width=True):
                            del ayarlar["kullanicilar"][kadi]
                            ayar_kaydet(ayarlar)
                            st.success("Öğretmen silindi!")
                            time.sleep(1); st.rerun()

        # --- SEKME 2: OKUL YÖNETİMİ VE BİRLEŞTİRME ---
        with tab_okul:
            st.markdown("#### 🔗 Hatalı / Mükerrer Okulları Birleştir")
            st.markdown('<div class="info-banner">Aynı okulun iki farklı isimle (Örn: "Atatürk OO" ve "Atatürk Ortaokulu") sisteme kaydedildiğini tespit ederseniz, hatalı olanı doğru olana aktarıp birleştirebilirsiniz. Hatalı okuldaki tüm öğrenci verileri, karne kayıtları ve öğretmenler otomatik olarak doğru okula transfer edilir ve hatalı okul listeden silinir.</div>', unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns(2)
            hatali_okul = col_b1.selectbox("Silinecek (Hatalı/Eski) Okul", ["— Seçiniz —"] + sorted(ayarlar["okullar"]))
            hedef_okul  = col_b2.selectbox("Aktarılacak (Doğru/Yeni) Okul", ["— Seçiniz —"] + sorted(ayarlar["okullar"]))

            if st.button("🔗 Okulları Birleştir ve Tüm Verileri Aktar", type="primary", use_container_width=True):
                if hatali_okul == "— Seçiniz —" or hedef_okul == "— Seçiniz —" or hatali_okul == hedef_okul:
                    st.error("Lütfen birleştirilecek iki farklı okulu seçin.")
                else:
                    with st.spinner("Veriler aktarılıyor..."):
                        # 1. Veritabanındaki tüm görev ve karnelerin okulunu güncelle
                        supabase.table('gorevler').update({'okul': hedef_okul}).eq('okul', hatali_okul).execute()
                        
                        # 2. Ayarlardaki öğretmenlerin okulunu güncelle
                        for k, u in ayarlar["kullanicilar"].items():
                            if u.get("okul") == hatali_okul:
                                ayarlar["kullanicilar"][k]["okul"] = hedef_okul
                        
                        # 3. Hatalı okulu sistem listesinden tamamen sil
                        if hatali_okul in ayarlar["okullar"]:
                            ayarlar["okullar"].remove(hatali_okul)
                        
                        ayar_kaydet(ayarlar)
                        st.cache_data.clear()
                        st.success(f"✅ Başarılı! '{hatali_okul}' sistemden silindi ve tüm verileri '{hedef_okul}' üzerine aktarıldı.")
                        time.sleep(2); st.rerun()

            st.markdown("---")
            st.markdown("#### ➕ Sisteme Manuel Yeni Okul Ekle")
            c_il, c_ilce, c_ok = st.columns(3)
            ekle_il = c_il.selectbox("İl Seçiniz", ["— Seçiniz —"] + TUM_ILLER, key="admin_ekle_il")
            ekle_ilce = c_ilce.text_input("İlçe Adı", key="admin_ekle_ilce").strip().title()
            ekle_okul = c_ok.text_input("Okul Adı", key="admin_ekle_okul").strip().title()
            
            if st.button("➕ Kurumu Ekle", type="primary"):
                if ekle_il == "— Seçiniz —" or not ekle_ilce or not ekle_okul:
                    st.error("Lütfen İl, İlçe ve Okul adını eksiksiz girin.")
                else:
                    tam_ad = f"{ekle_il} / {ekle_ilce} / {ekle_okul}"
                    if tam_ad not in ayarlar["okullar"]:
                        ayarlar["okullar"].append(tam_ad)
                        ayar_kaydet(ayarlar)
                        st.success(f"✅ '{tam_ad}' listeye eklendi!")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning("Bu okul zaten listede mevcut.")
                        
        st.markdown('</div>', unsafe_allow_html=True)
    # ══════════════════════════════════════════════════
    # SEKME: AYARLAR & PROFİL
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ayarlar":
        if rol == "admin" and not admin_bakis:
            render_nav_bar(ALT_MENU_AYARLAR_ADMIN, "nav_ayar_alt", is_main=False)
        else:
            render_nav_bar(ALT_MENU_AYARLAR_OGRT, "nav_ayar_alt", is_main=False)
        aktif_ayar = st.session_state.get("nav_ayar_alt", "sistem" if (rol == "admin" and not admin_bakis) else "profil")

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        if aktif_ayar == "sistem" and rol == "admin":
            st.markdown("<div class='section-header'>🔒 Sistem Kontrolü</div>", unsafe_allow_html=True)
            kilitli = st.checkbox("Sistemi Öğretmen Girişine Kapat", value=ayarlar.get("sistem_kilitli", False))
            if kilitli != ayarlar.get("sistem_kilitli", False):
                ayarlar["sistem_kilitli"] = kilitli
                ayar_kaydet(ayarlar)
                st.rerun()
            st.markdown("---")
            st.markdown("**Mevcut Durum:**")
            if kilitli:
                st.error("🔒 Sistem şu anda öğretmen girişine KAPALI.")
            else:
                st.success("✅ Sistem açık — öğretmenler giriş yapabilir.")

        elif aktif_ayar == "okullar" and rol == "admin":
            st.markdown("<div class='section-header'>🏢 Okul Listesi ve Hiyerarşi Yönetimi</div>", unsafe_allow_html=True)
            
            tab_okul_ekle, tab_okul_birlestir = st.tabs(["➕ Yeni Okul Ekle / Sil", "🔗 Mükerrer Okulları Birleştir"])

            with tab_okul_ekle:
                st.markdown("Sisteme Türkiye genelinden yeni bir okul eklemek için aşağıdaki alanları kullanın:")
                c_il, c_ilce, c_ok = st.columns(3)
                
                ekle_il = c_il.selectbox("İl Seçiniz", ["— Seçiniz —"] + TUM_ILLER, key="admin_ekle_il")
                ekle_ilce = c_ilce.text_input("İlçe Adı", key="admin_ekle_ilce").strip().title()
                ekle_okul = c_ok.text_input("Okul Adı", key="admin_ekle_okul").strip().title()
                
                if st.button("➕ Kurumu Ekle", type="primary"):
                    if ekle_il == "— Seçiniz —" or not ekle_ilce or not ekle_okul:
                        st.error("Lütfen İl, İlçe ve Okul adını eksiksiz girin.")
                    else:
                        tam_ad = f"{ekle_il} / {ekle_ilce} / {ekle_okul}"
                        if tam_ad not in ayarlar["okullar"]:
                            ayarlar["okullar"].append(tam_ad)
                            ayar_kaydet(ayarlar)
                            st.success(f"✅ '{tam_ad}' listeye eklendi!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("Bu okul zaten listede mevcut.")
                
                st.markdown("---")
                st.markdown("**Kayıtlı Okulları Sil:**")
                sil_okul = st.selectbox("Silinecek Okulu Seç", ["— Seçiniz —"] + sorted(ayarlar["okullar"]))
                if st.button("🗑️ Seçili Okulu Listeden Çıkar"):
                    if sil_okul != "— Seçiniz —":
                        ayarlar["okullar"].remove(sil_okul)
                        ayar_kaydet(ayarlar)
                        st.success("Silindi.")
                        time.sleep(1)
                        st.rerun()

            with tab_okul_birlestir:
                st.markdown("#### 🔗 Hatalı veya Farklı Yazılan Okulları Birleştir")
                st.markdown('<div class="info-banner">Örn: Eski düz isimli "Gazi Ortaokulu"nu yeni formatlı "Mardin / Dargeçit / Gazi Ortaokulu" ile birleştirebilirsiniz. Hatalı okuldaki tüm öğretmen ve öğrenciler otomatik olarak doğru okula aktarılır.</div>', unsafe_allow_html=True)
                
                col_b1, col_b2 = st.columns(2)
                
                hatali_okul = col_b1.selectbox("Silinecek (Hatalı/Eski) Okul", ["— Seçiniz —"] + sorted(ayarlar["okullar"]))
                hedef_okul  = col_b2.selectbox("Aktarılacak (Doğru/Yeni) Okul", ["— Seçiniz —"] + sorted(ayarlar["okullar"]))

                if st.button("🔗 Okulları Birleştir ve Verileri Aktar", type="primary", use_container_width=True):
                    if hatali_okul == "— Seçiniz —" or hedef_okul == "— Seçiniz —" or hatali_okul == hedef_okul:
                        st.error("Lütfen iki farklı okul seçin.")
                    else:
                        supabase.table('gorevler').update({'okul': hedef_okul}).eq('okul', hatali_okul).execute()
                        
                        for k, u in ayarlar["kullanicilar"].items():
                            if u.get("okul") == hatali_okul:
                                ayarlar["kullanicilar"][k]["okul"] = hedef_okul
                        
                        if hatali_okul in ayarlar["okullar"]:
                            ayarlar["okullar"].remove(hatali_okul)
                            
                        ayar_kaydet(ayarlar)
                        st.success(f"✅ '{hatali_okul}' isimli okul listeden silindi! İçindeki tüm veriler '{hedef_okul}' okuluna aktarıldı.")
                        time.sleep(2)
                        st.rerun()

        elif aktif_ayar == "sablonlar":
            sablon_yonetimi_ui(ayarlar, kb, rol)

        elif aktif_ayar == "profil":
            st.markdown("<div class='section-header'>👤 Kişisel Profil Ayarları</div>", unsafe_allow_html=True)
            with st.form("profil_form"):
                p_ad     = st.text_input("Ad Soyad", value=kb.get("ad", ""))
                p_brans  = st.text_input("Branş", value=kb.get("brans",""))
                p_eposta = st.text_input("E-posta Adresiniz", value=kb.get("eposta",""))
                p_sifre  = st.text_input("Yeni Şifre (boş bırakırsan değişmez)", type="password")
                
                st.markdown("---")
                st.markdown("**🔑 Kişisel Yapay Zeka Anahtarı (Opsiyonel)**")
                st.info("Sistemin yoğun olduğu dönemlerde (karne haftası) beklemeden hızlıca işlem yapmak için kendi ücretsiz Google Gemini API anahtarınızı buraya girebilirsiniz. Sistem önce sizin anahtarınızı kullanır, boş bırakırsanız okul havuzunu kullanır. [Nasıl alınır öğrenmek için tıklayın](https://aistudio.google.com/app/apikey)")
                p_api = st.text_input("Gemini API Anahtarınız", value=kb.get("api_key",""), type="password", placeholder="AIzaSy ile başlayan anahtarı yapıştırın...")
                
                if st.form_submit_button("💾 Bilgilerimi Güncelle"):
                    guncelleme = {"ad": p_ad, "brans": p_brans, "eposta": p_eposta, "api_key": p_api.strip()}
                    if p_sifre.strip():
                        guncelleme["sifre"] = p_sifre
                    ayarlar["kullanicilar"][aktif_id].update(guncelleme)
                    ayar_kaydet(ayarlar)
                    st.session_state["kullanici_bilgi"] = ayarlar["kullanicilar"][aktif_id]
                    st.success("✅ Profiliniz güncellendi!")


# ==========================================
# 16. FOOTER
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
        <div style="margin-top:8px;font-size:0.78rem;">
            © 2025 PUSULA 360. Tüm hakları saklıdır.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 17. ANA ÇALIŞTIRMA
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df      = veri_yukle()

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
