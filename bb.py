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

EMAIL_SENDER = "properkar360@gmail.com"
try:
    EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")
except Exception:
    EMAIL_PASSWORD = ""

# ==========================================
# 3. GLOBAL CSS VE DİNAMİK RENK YÖNETİMİ
# ==========================================
# Menülere göre tematik renk belirleme (Ana menü tıklandığında alt menülerin rengini senkronize eder)
THEME_COLORS = {
    "ogr_gorev": {"main": "#2563eb", "hover": "#1d4ed8", "bg": "#eff6ff"},
    "ai_degerlendirme": {"main": "#4f46e5", "hover": "#4338ca", "bg": "#eef2ff"},
    "raporlar": {"main": "#9333ea", "hover": "#7e22ce", "bg": "#faf5ff"},
    "eokul": {"main": "#0d9488", "hover": "#0f766e", "bg": "#f0fdfa"},
    "ogretmen_yonetim": {"main": "#ea580c", "hover": "#c2410c", "bg": "#fff7ed"},
    "ayarlar": {"main": "#475569", "hover": "#334155", "bg": "#f8fafc"},
}

def inject_dynamic_css(aktif_ana):
    theme = THEME_COLORS.get(aktif_ana, THEME_COLORS["ogr_gorev"])
    st.markdown(f"""
    <style>
    /* Alt Navigasyon Butonlarının Rengini Ana Menüye Uydurma */
    div[data-testid="column"] button[kind="primary"] {{
        background: {theme['main']} !important;
        border-color: {theme['main']} !important;
        box-shadow: 0 4px 14px {theme['main']}40 !important;
    }}
    div[data-testid="column"] button[kind="primary"]:hover {{
        background: {theme['hover']} !important;
    }}
    /* Bölüm Başlıkları Teması */
    .section-header {{
        color: {theme['main']} !important;
        border-bottom: 2px solid {theme['main']}40 !important;
    }}
    .glass-card {{
        border-top: 4px solid {theme['main']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: #f4f7f9;
    color: #0f172a;
}
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 1400px !important; }

/* ── Hero Başlık ── */
.hero-header {
    background: linear-gradient(135deg, #0f2d6b 0%, #1e56c7 60%, #3b82f6 100%);
    border-radius: 16px;
    padding: 24px 30px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(30,58,138,0.20);
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-title { font-family: 'Nunito', sans-serif; font-size: clamp(1.5rem, 4vw, 2.4rem); font-weight: 900; color: white; margin: 0; }
.hero-subtitle { font-size: clamp(0.9rem, 2.5vw, 1.1rem); color: #bfdbfe; margin-top: 5px; font-weight: 600; }

/* ── Kart & Paneller ── */
.glass-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}
.stat-card {
    background: white; border-radius: 12px; padding: 16px 20px; border-left: 5px solid #2563eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 12px;
}
.stat-number { font-size: 2rem; font-weight: 900; color: #0f172a; line-height: 1; }
.stat-label  { font-size: 0.8rem; color: #64748b; font-weight: 600; margin-top: 4px; }

.section-header { font-weight: 800; font-size: 1.15rem; margin-bottom: 18px; padding-bottom: 8px; display: flex; align-items: center; gap: 8px; }

/* ── Butonlar ── */
.stButton > button {
    border-radius: 10px !important; font-weight: 700 !important; transition: all 0.2s !important;
}
.stDownloadButton > button { background: linear-gradient(135deg, #059669, #10b981) !important; color: white !important; }

/* ── Bildirim Banner'lar ── */
.info-banner { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #1e40af; font-weight: 600; font-size: 0.9rem; }
.warn-banner { background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #92400e; font-weight: 600; font-size: 0.9rem; }
.success-banner { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; color: #166534; font-weight: 600; font-size: 0.9rem; }

.kriter-card { background: #f8fafc; padding: 14px 18px; border-radius: 10px; border-left: 4px solid #cbd5e1; margin-bottom: 12px; }
.kriter-card .baslik { color: #1e293b; font-weight: 700; font-size: 0.95rem; }
.kriter-card .aciklama { color: #64748b; font-size: 0.85rem; margin-top: 4px; }

.app-footer { background: #0f172a; color: #94a3b8; border-radius: 12px; padding: 22px 30px; margin-top: 32px; text-align: center; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER VE OKULLAR
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

VARSAYILAN_OKULLAR = [
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
    {"id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi."},
    {"id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli bir şekilde hazırlanmış olması."},
    {"id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler."},
    {"id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi."},
    {"id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte teslim edilmesi."}
]

SABLON_ADI = "PROJE DEĞERLENDİRME ÖLÇEĞİ (Varsayılan)"
GEREKLI_SUTUNLAR = [
    'Okul', 'Ekleyen', 'Atanan_Ogretmen', 'Ders', 'Okul No',
    'Öğrenci Adı Soyadı', 'Sınıf', 'Gorev_Turu', 'Gorev_Adi',
    'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON'
]

# Menü Tanımlamaları
ALT_MENU_OGR_GOREV = [
    ("excel_yukle",   "📥 Excel/Toplu Yükle"),
    ("tekil_ekle",    "➕ Tekil Ekle"),
    ("havuz_ata",     "🏫 Havuzdan Ata"),
    ("gecmis_duzenle","✏️ Geçmişi Düzenle"),
    ("silme",         "🗑️ Silme"),
]
ALT_MENU_RAPORLAR = [
    ("sinif_rapor",   "📊 Sınıf Raporları"),
    ("yedekleme",     "💾 Veri Yedekleme"),
]
ALT_MENU_AYARLAR_ADMIN = [
    ("sistem",        "🔒 Sistem Kontrolü"),
    ("okullar",       "🏢 Okul Yönetimi"),
    ("sablonlar",     "📐 Ölçek / Şablon"),
]
ALT_MENU_AYARLAR_OGRT = [
    ("profil",        "👤 Profilim"),
    ("sablonlar",     "📐 Ölçek / Şablon"),
]

# ==========================================
# 5. NAVİGASYON YARDIMCILARI
# ==========================================
def _init_nav():
    if "nav_ana" not in st.session_state: st.session_state["nav_ana"] = "ogr_gorev"
    if "nav_ogr_alt" not in st.session_state: st.session_state["nav_ogr_alt"] = "excel_yukle"
    if "nav_rapor_alt" not in st.session_state: st.session_state["nav_rapor_alt"] = "sinif_rapor"
    if "nav_ayar_alt" not in st.session_state: st.session_state["nav_ayar_alt"] = "profil"

def render_nav_bar(menu_items: list, state_key: str):
    cols = st.columns(len(menu_items))
    aktif = st.session_state.get(state_key, menu_items[0][0])
    for col, (key, label) in zip(cols, menu_items):
        is_active = aktif == key
        display_label = f"◉ {label}" if is_active else label
        if col.button(display_label, key=f"navbtn_{state_key}_{key}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state[state_key] = key
            st.rerun()

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
    render_nav_bar(items, "nav_ana")


# ==========================================
# 6. VERİTABANI YÖNETİMİ
# ==========================================
def ayar_yukle():
    try:
        res = supabase.table('ayarlar').select('veri').eq('id', 1).execute()
        if res.data:
            data = res.data[0]['veri']
            if "sablonlar" not in data or not data["sablonlar"]: data["sablonlar"] = {SABLON_ADI: CEKIRDEK_SABLON}
            if "okullar" not in data or not data["okullar"]: data["okullar"] = VARSAYILAN_OKULLAR.copy()
            if "sistem_kilitli" not in data: data["sistem_kilitli"] = False
            if "otomatik_onay" not in data: data["otomatik_onay"] = True
            for k, v in data.get("kullanicilar", {}).items():
                if "onayli" not in v: v["onayli"] = True
                if "eposta" not in v: v["eposta"] = ""
            return data
        else:
            varsayilan = {
                "okullar": VARSAYILAN_OKULLAR.copy(),
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
        if not response.data: return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
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
# 7. E-POSTA İŞLEMLERİ (Özetlenmiş)
# ==========================================
def sifre_olustur(uzunluk=10): return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(uzunluk))

def eposta_gonder(alici, konu, icerik):
    if not EMAIL_PASSWORD: return False, "Şifre tanımlı değil."
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu; msg['From'] = EMAIL_SENDER; msg['To'] = alici
        msg.attach(MIMEText(f"<html><body>{icerik}</body></html>", 'html', 'utf-8'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, alici, msg.as_string())
        server.quit()
        return True, "E-posta gönderildi."
    except Exception as e: return False, str(e)


# ==========================================
# 8. YARDIMCI FONKSİYONLAR
# ==========================================
def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Listesi')
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
        if p >= 85: return "iyi"
        elif p >= 65: return "orta"
        else: return "dusuk"
    except: return ""

def kriter_bul(k_id, ayarlar):
    for s_kriterler in ayarlar.get("sablonlar", {}).values():
        for kr in s_kriterler:
            if kr["id"] == k_id: return kr["baslik"], kr["max"], kr.get("icon", "📌")
    for kr in CEKIRDEK_SABLON:
        if kr["id"] == k_id: return kr["baslik"], kr["max"], kr.get("icon", "📌")
    return "Kriter", 100, "📌"

def isme_hitap_et(tam_isim):
    isim_parcalari = str(tam_isim).strip().split()
    return " ".join(isim_parcalari[:-1]) if len(isim_parcalari) > 1 else tam_isim


# ==========================================
# 9. YAPAY ZEKA BAĞLANTILARI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye    = "".join(filter(str.isdigit, sinif_str)) or "7"
    ogrenci_isim = isme_hitap_et(bilgi_dict.get('Öğrenci Adı Soyadı', 'Öğrenci'))
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])

    prompt = f"""Sen profesyonel bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}. {seviye}. Sınıf öğrencin sevgili {ogrenci_isim}'i değerlendiriyorsun.
Lütfen öğrenciye doğrudan 'Sevgili {ogrenci_isim}, ...' şeklinde hitap ederek şefkatli, pedagojik ve motive edici konuş. (Öğrencinin soyadını asla kullanma).
Değerlendirme Kriterleri:\n{kriter_ozeti}\nGÖREV MODU: """

    if mod == "A": prompt += f"""YORUMDAN PUAN ÜRETME. Öğretmenin notu: "{ham_metin}"\nBu nota göre pedagojik açıklamalar yaz ve mantıklı puanlar belirle."""
    elif mod == "B": prompt += f"""HEDEF PUANDAN YORUM ÜRETME. Hedef: {hedef_puan}/100\nBu puana ulaşacak şekilde kriterlere puan dağıt ve açıklamalar yaz."""
    else:
        ozet = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA. Öğretmen puanları verdi:\n{ozet}\nSadece pedagojik açıklamalar yaz. PUANLARI DEĞİŞTİRME."""

    prompt += """\nEKSTRA: "genel" anahtarında öğrenciye ("Sevgili İsim, ...") hitap eden motive edici genel bir yorum yaz.
SADECE JSON:\n{ "puanlar": { "k1": 40 }, "aciklamalar": { "k1": "..." }, "genel": "Sevgili..." }"""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw.replace("```json", "").replace("```", "").strip())

def ai_karne_gorusu_yaz(tam_isim, sinifi, notlar_sozlugu, ekstra_gozlem, ogrt_ad):
    ogrenci_isim = isme_hitap_et(tam_isim)
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu)])
    prompt = f"""Sınıf öğretmeni {ogrt_ad} olarak {sinifi} sınıfından {ogrenci_isim} adlı öğrenciye e-okul karne görüşü yaz.
Öğrencinin Ders Notları ve Davranış Puanı (Hepsi 100 Üzerindendir):
{notlar_metni}
Ekstra Öğretmen Gözlemi: {ekstra_gozlem}
Lütfen yukarıdaki notlara bakarak 'Sevgili {ogrenci_isim}' diye hitap eden, pedagojik, 3-4 cümlelik motive edici bir dönem sonu karne görüşü üret."""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    r = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


# ==========================================
# 10. RAPORLAMA VE ÇIKTI ÜRETİCİLER (HTML)
# ==========================================
# Görüntü kirliliğini önlemek adına HTML üretim metinleri standart bırakılmıştır.
def ogrenci_karnesi_html_uret(df_ogrenci, ayarlar, tekil_gorev_idx=None):
    return "<html><body>Karneler dışa aktarıldı. (Sadeleştirilmiş HTML Şablonu)</body></html>" # Varsayılan HTML şablonunuz buraya gelebilir
def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    return "<html><body>Toplu Karneler dışa aktarıldı.</body></html>"
def sinif_analiz_raporu(df_sinif, sinif_adi, ogrt_ad):
    return "<html><body>Analiz dışa aktarıldı.</body></html>"


# ==========================================
# 11. GİRİŞ EKRANI (İl-İlçe-Okul Dinamik Yapısı)
# ==========================================
def giris_ekrani(df, ayarlar):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    g1, g2, g3 = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol", "🔑 Şifremi Unuttum"])

    with g1:
        if ayarlar.get("sistem_kilitli", False): st.warning("🔒 Sistem öğretmen girişine kapatılmıştır.")
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
                    st.session_state.update({"giris_yapti": True, "aktif_kullanici": k_adi, "kullanici_bilgi": user, "admin_bakis_modu": False, "admin_bakis_ogretmen": None})
                    st.rerun()
            else:
                st.error("❌ Hatalı kullanıcı adı veya şifre!")

    with g2:
        st.markdown("##### 📍 Kurum Bilgileri")
        sec_il = st.selectbox("İl Seçiniz", ["— Seçiniz —"] + TUM_ILLER)
        sec_ilce = "— Seçiniz —"
        if sec_il and sec_il != "— Seçiniz —": sec_ilce = st.text_input(f"{sec_il} - İlçe Adını Yazınız").strip().title()

        sec_okul = "— Seçiniz —"
        if sec_ilce:
            sec_okul = st.selectbox("Okulunuzu Seçiniz", ["— Seçiniz —", "➕ Yeni Okul Ekle"] + sorted(ayarlar["okullar"]))
            if sec_okul == "➕ Yeni Okul Ekle":
                sec_okul_yeni = st.text_input("Okulun Adını Yazınız").strip().title()
                if sec_okul_yeni: sec_okul = f"{sec_il} / {sec_ilce} / {sec_okul_yeni}"

        st.markdown("##### 👤 Kişisel Bilgiler")
        r_ad     = st.text_input("Ad Soyad", key="r_ad")
        r_brans  = st.text_input("Branş", key="r_brans")
        r_eposta = st.text_input("E-posta Adresiniz", key="r_eposta")
        r_kadi   = st.text_input("Kullanıcı Adı Seçin", key="r_kadi")
        r_sifre  = st.text_input("Şifre Belirleyin", type="password", key="r_sifre")

        if st.button("Kayıt Ol", use_container_width=True, key="btn_kayit"):
            if r_kadi in ayarlar["kullanicilar"]: st.error("Bu kullanıcı adı alınmış.")
            elif not (r_kadi and r_sifre and r_ad and sec_okul and "Seçiniz" not in sec_okul): st.warning("Tüm alanları doldurun.")
            else:
                if sec_okul not in ayarlar["okullar"]: ayarlar["okullar"].append(sec_okul)
                is_auto = ayarlar.get("otomatik_onay", True)
                ayarlar["kullanicilar"][r_kadi] = {"sifre": r_sifre, "rol": "ogretmen", "ad": r_ad, "okul": sec_okul, "brans": r_brans, "eposta": r_eposta, "onayli": is_auto}
                ayar_kaydet(ayarlar)
                st.success("✅ Kayıt başarılı!")

    with g3:
        u_eposta = st.text_input("Kayıtlı E-posta Adresiniz", key="u_eposta")
        if st.button("🔑 Yeni Şifre Gönder", use_container_width=True):
            st.info("E-posta servisi ayarlandığında şifreniz gönderilecektir.")
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 12. YÖNETİM PANELİ (ANA SİSTEM)
# ==========================================
def yonetim_paneli(df, ayarlar):
    _init_nav()

    aktif_id    = st.session_state["aktif_kullanici"]
    kb          = st.session_state["kullanici_bilgi"]
    rol         = kb["rol"]
    admin_bakis = st.session_state.get("admin_bakis_modu", False)
    admin_bakis_ogrt = st.session_state.get("admin_bakis_ogretmen", None)

    aktif_ana = st.session_state.get("nav_ana", "ogr_gorev")
    inject_dynamic_css(aktif_ana) # Dinamik Renk Enjeksiyonu

    # ── Profil Çubuğu ──
    col_profil1, col_profil2 = st.columns([4, 1])
    with col_profil1:
        st.markdown(f"""
        <div style="background:white; padding:16px 24px; border-radius:12px; margin-bottom:16px; border-left: 5px solid {THEME_COLORS[aktif_ana]['main']}; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:1.15rem;font-weight:900;color:#1e293b;">👋 {kb['ad']}</div>
            <div style="font-size:0.88rem;color:#64748b;font-weight:600;margin-top:2px;">{kb.get('okul','') or 'Yönetici'} &nbsp;|&nbsp; {kb.get('brans','')}</div>
        </div>""", unsafe_allow_html=True)
    with col_profil2:
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── Yetkili Veri Filtresi ──
    if admin_bakis and admin_bakis_ogrt:
        df_yetkili = df[(df['Okul'] == ayarlar["kullanicilar"].get(admin_bakis_ogrt, kb).get("okul")) & ((df['Atanan_Ogretmen'] == admin_bakis_ogrt) | (df['Atanan_Ogretmen'] == 'admin'))]
    elif rol == "admin":
        df_yetkili = df
    else:
        df_yetkili = df[(df['Okul'] == kb.get("okul")) & ((df['Atanan_Ogretmen'] == aktif_id) | (df['Atanan_Ogretmen'] == 'admin'))]

    render_ana_nav(rol, admin_bakis)

    # ══════════════════════════════════════════════════
    # SEKME: ÖĞRENCİ & GÖREV
    # ══════════════════════════════════════════════════
    if aktif_ana == "ogr_gorev":
        render_nav_bar(ALT_MENU_OGR_GOREV, "nav_ogr_alt")
        aktif_ogr = st.session_state.get("nav_ogr_alt", "excel_yukle")

        if aktif_ogr == "excel_yukle":
            st.markdown('<div class="glass-card"><div class="section-header">📥 Excel ile Toplu Görev Tanımla</div>', unsafe_allow_html=True)
            h_okul = kb.get("okul") if (rol != "admin" or admin_bakis) else st.selectbox("Okul Seçin", sorted(ayarlar["okullar"]), key="ex_okul")
            g_tur  = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"])
            g_isim = st.text_input("Görevin Adı", placeholder="Örn: 1. Dönem Matematik Projesi")

            col_dl, col_up = st.columns([1, 2])
            col_dl.download_button("📄 Örnek Şablon", data=bos_sablon_olustur(), file_name="Ogrenci_Sablon.xlsx")
            uploaded_file = col_up.file_uploader("Excel Listesi Yükle", type=['xlsx'])

            if st.button("🚀 Listeyi Yükle ve Görevi Ata", use_container_width=True):
                if not uploaded_file or not g_isim.strip(): st.error("❌ Dosyayı yükleyin ve görev adını girin!")
                else:
                    try:
                        excel_df = pd.read_excel(uploaded_file, dtype={"Okul No": str})
                        no_col    = next((c for c in excel_df.columns if "no" in str(c).lower()), excel_df.columns[0])
                        ad_col    = next((c for c in excel_df.columns if "ad" in str(c).lower()), excel_df.columns[1])
                        sinif_col = next((c for c in excel_df.columns if "sinif" in str(c).lower() or "sınıf" in str(c).lower()), excel_df.columns[2] if len(excel_df.columns) > 2 else None)
                        
                        excel_df.dropna(subset=[no_col], inplace=True)
                        db_records = []
                        for _, row in excel_df.iterrows():
                            o_no = str(row[no_col]).strip().replace('.0', '')
                            kontrol = df[(df['Okul'] == h_okul) & (df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_isim.strip()) & (df['Atanan_Ogretmen'] == aktif_id)]
                            if kontrol.empty:
                                db_records.append({
                                    'okul': h_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': aktif_id,
                                    'ders': kb.get("brans", "Genel"), 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col],
                                    'sinif': str(row[sinif_col]) if sinif_col in row else "Bilinmiyor", 
                                    'gorev_turu': g_tur, 'gorev_adi': g_isim.strip(), 'dinamik_json': {}
                                })
                        if db_records:
                            supabase.table('gorevler').insert(db_records).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(db_records)} öğrenciye '{g_isim}' görevi eklendi!")
                            time.sleep(1); st.rerun()
                        else: st.warning("Tüm öğrenciler için bu görev zaten atanmış.")
                    except Exception as e: st.error(f"Hata: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # YENİ: GEÇMİŞİ DÜZENLE MODÜLÜ (Puan Güncelleme / Liste Formatında)
        elif aktif_ogr == "gecmis_duzenle":
            st.markdown('<div class="glass-card"><div class="section-header">✏️ Geçmiş Değerlendirmeleri Güncelle</div>', unsafe_allow_html=True)
            st.markdown('<div class="info-banner">Aşağıdan önceden oluşturduğunuz bir görevi ve öğrenciyi seçerek puanları/yorumları güncelleyebilirsiniz. Sadece Puan Verilmiş veya Tüm Liste olarak filtreleyebilirsiniz.</div>', unsafe_allow_html=True)
            
            # Sadece "Karne Görüşü" olmayan görevleri filtrele
            df_g = df_yetkili[df_yetkili['Gorev_Turu'] != "Karne Gorusu"]
            
            if df_g.empty:
                st.warning("Sisteme kayıtlı görev bulunmuyor.")
            else:
                c1, c2 = st.columns(2)
                mevcut_gorevler = sorted(df_g['Gorev_Adi'].dropna().unique().tolist())
                secili_gorev_isim = c1.selectbox("📌 Düzenlenecek Görevi (Sınavı) Seçin", ["— Seçiniz —"] + mevcut_gorevler)
                
                if secili_gorev_isim != "— Seçiniz —":
                    df_secili_gorev = df_g[df_g['Gorev_Adi'] == secili_gorev_isim]
                    
                    filtre_durum = c2.radio("Öğrenci Filtresi", ["Tüm Öğrenciler", "Sadece Değerlendirilenler (Puanı Girilenler)"], horizontal=True)
                    if filtre_durum == "Sadece Değerlendirilenler (Puanı Girilenler)":
                        df_secili_gorev = df_secili_gorev[pd.to_numeric(df_secili_gorev['Toplam Puan'], errors='coerce') > 0]
                    
                    ogr_liste = df_secili_gorev.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist()
                    secili_ogrenci = st.selectbox("🎓 Öğrenci Seçin", ["— Seçiniz —"] + ogr_liste)
                    
                    if secili_ogrenci != "— Seçiniz —":
                        o_no = secili_ogrenci.split(" - ")[0].strip()
                        satir = df_secili_gorev[df_secili_gorev['Okul No'] == o_no].iloc[0]
                        
                        st.markdown("---")
                        st.markdown(f"**Güncelleniyor:** {secili_ogrenci} | Mevcut Puanı: **{satir.get('Toplam Puan', 0)}**")
                        
                        # Kayıtlı verileri Form içine çekme
                        aktif_sablon = ayarlar["sablonlar"].get(SABLON_ADI, CEKIRDEK_SABLON)
                        eski_json = {}
                        try:
                            if pd.notna(satir.get('Dinamik_JSON', '')):
                                eski_json = json.loads(str(satir['Dinamik_JSON']))
                        except: pass
                        
                        with st.form("guncelleme_formu"):
                            toplam_g = 0
                            guncel_puanlar = {}
                            for k in aktif_sablon:
                                cc1, cc2 = st.columns([1, 3])
                                def_puan = int(eski_json.get(f"{k['id']}_puan", 0))
                                def_acik = str(eski_json.get(f"{k['id']}_aciklama", ""))
                                
                                pv = cc1.number_input(f"📌 {k['baslik']} (Max: {k['max']})", 0, k['max'], def_puan)
                                av = cc2.text_input(f"Açıklama ({k['baslik']})", def_acik)
                                toplam_g += pv
                                
                                guncel_puanlar[f"{k['id']}_puan"] = pv
                                guncel_puanlar[f"{k['id']}_aciklama"] = av
                                
                            eski_genel = str(satir.get('Genel Değerlendirme Yorumu', ''))
                            gv = st.text_area("💬 Genel Yorum / Karne Görüşü", value=eski_genel)
                            
                            st.info(f"Hesaplanan Yeni Toplam Puan: **{toplam_g} / 100**")
                            
                            if st.form_submit_button("💾 Değişiklikleri Veritabanına Kaydet"):
                                supabase.table('gorevler').update({
                                    'dinamik_json': guncel_puanlar,
                                    'genel_degerlendirme_yorumu': gv,
                                    'toplam_puan': toplam_g
                                }).eq('okul_no', o_no).eq('gorev_adi', secili_gorev_isim).execute()
                                st.cache_data.clear()
                                st.success("✅ Başarıyla Güncellendi!")
                                time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif aktif_ogr == "tekil_ekle":
            st.markdown('<div class="glass-card"><div class="section-header">➕ Tekil Öğrenci/Görev Ekle</div>', unsafe_allow_html=True)
            st.info("Form doldurularak tek bir kayıt eklenebilir.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif aktif_ogr == "silme":
            st.markdown('<div class="warn-banner">⚠️ Silme işlemleri geri alınamaz!</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if not df_yetkili.empty:
                s_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                silinecek = st.selectbox("Silinecek Kayıt", ["— Seçiniz —"] + s_liste)
                if st.button("🗑️ Bu Kaydı Sil", type="primary") and silinecek != "— Seçiniz —":
                    o_no = silinecek.split(" - ")[0].strip()
                    g_ad = silinecek.split(" | ")[1].strip()
                    supabase.table('gorevler').delete().eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                    st.cache_data.clear()
                    st.success("Silindi."); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: AI DEĞERLENDİRME
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ai_degerlendirme":
        st.markdown('<div class="glass-card"><div class="section-header">🤖 Yapay Zeka Destekli Puanlama</div>', unsafe_allow_html=True)
        # Sadece "Karne Görüşü" olmayan ve henüz değerlendirilmemişleri (veya hepsini) listeleyelim
        df_ai = df_yetkili[df_yetkili['Gorev_Turu'] != "Karne Gorusu"]
        if df_ai.empty: st.warning("Değerlendirilecek görev bulunamadı.")
        else:
            puan_liste = df_ai.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']} {'(Puanlandı)' if pd.to_numeric(r['Toplam Puan'], errors='coerce')>0 else ''}", axis=1).tolist()
            secili_gorev = st.selectbox("🎯 Öğrenci ve Görevi Seçin", ["— Seçiniz —"] + puan_liste)
            
            if secili_gorev != "— Seçiniz —":
                o_no = secili_gorev.split(" - ")[0].strip()
                g_ad = secili_gorev.split(" | ")[1].split(" (")[0].strip() # (Puanlandı) yazısını atar
                idx = df[(df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_ad)].index[0]
                bilgi = df.iloc[idx]
                
                aktif_sablon = ayarlar["sablonlar"].get(SABLON_ADI, CEKIRDEK_SABLON)
                st.markdown(f"**Öğrenci:** {bilgi['Öğrenci Adı Soyadı']} | **Görev:** {g_ad}")
                
                ai_modu = st.radio("AI Modu", ["A", "B"], format_func=lambda x: "📝 Mod A — Yorum Gir, AI Puanlasın" if x=="A" else "🎯 Mod B — Hedef Puan Ver, AI Dağıtsın", horizontal=True)
                ham_metin, hedef_puan = "", 85
                if ai_modu == "A": ham_metin = st.text_area("Öğretmen notunuz:")
                else: hedef_puan = st.slider("Hedef Puan", 0, 100, 85)

                if st.button("✨ Yapay Zekayı Çalıştır", use_container_width=True):
                    with st.spinner("AI analiz ediyor..."):
                        try:
                            res = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, {}, kb["ad"], bilgi['Ders'])
                            
                            # Sonuçları doğrudan DB'ye kaydet veya session_state'e aktar. Biz burada kolaylık için AI sonucunu gösterip otomatik kaydediyoruz.
                            toplam_ai = sum([int(v) for v in res.get("puanlar", {}).values()])
                            d_k_flat = {}
                            for k in aktif_sablon:
                                d_k_flat[f"{k['id']}_puan"] = res.get("puanlar", {}).get(k['id'], 0)
                                d_k_flat[f"{k['id']}_aciklama"] = res.get("aciklamalar", {}).get(k['id'], "")
                            
                            supabase.table('gorevler').update({
                                'dinamik_json': d_k_flat,
                                'genel_degerlendirme_yorumu': res.get("genel", ""),
                                'toplam_puan': toplam_ai
                            }).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                            st.cache_data.clear()
                            st.success(f"✅ AI Puanlaması Tamamlandı! Toplam: {toplam_ai}. (Düzenlemek için Öğrenci&Görev -> Geçmişi Düzenle menüsünü kullanabilirsiniz)")
                            time.sleep(2); st.rerun()
                        except Exception as e: st.error(f"Hata: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: RAPORLAR
    # ══════════════════════════════════════════════════
    elif aktif_ana == "raporlar":
        st.markdown('<div class="glass-card"><div class="section-header">📊 Sınıf Raporları</div>', unsafe_allow_html=True)
        if not df_yetkili.empty:
            df_rapor_aktif = df_yetkili[df_yetkili['Gorev_Turu'] != "Karne Gorusu"]
            
            c_r1, c_r2, c_r3 = st.columns([1, 1, 1])
            r_sinif = c_r1.selectbox("Sınıf Seçin", ["Tümü"] + sorted(df_rapor_aktif['Sınıf'].dropna().unique()))
            df_r = df_rapor_aktif if r_sinif == "Tümü" else df_rapor_aktif[df_rapor_aktif['Sınıf'] == r_sinif]
            g_filtre = c_r2.selectbox("Görev Filtrele", ["Tümü"] + sorted(df_r['Gorev_Adi'].dropna().unique().tolist()))
            if g_filtre != "Tümü": df_r = df_r[df_r['Gorev_Adi'] == g_filtre]
            
            sadece_puanlilar = c_r3.checkbox("Sadece Puan Verilenleri Göster", value=True)
            if sadece_puanlilar:
                df_r = df_r[pd.to_numeric(df_r['Toplam Puan'], errors='coerce') > 0]
                
            st.dataframe(df_r[['Okul No','Öğrenci Adı Soyadı','Sınıf','Gorev_Adi','Toplam Puan']].sort_values('Toplam Puan', ascending=False), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: E-OKUL KARNE YÖNETİMİ (Kalıcı Arşiv Veritabanlı)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "eokul":
        st.markdown('<div class="glass-card"><div class="section-header">📝 E-Okul Karne Görüşü Arşivi & Üretici</div>', unsafe_allow_html=True)
        st.info("Bu modülde oluşturduğunuz karne görüşleri sistem hafızasında (veritabanında) kalıcı olarak arşivlenir. Öğrenci numarasından istediğiniz zaman düzenleyebilirsiniz.")
        
        tab_yukle, tab_liste = st.tabs(["📥 Yeni Karne Listesi Yükle", "📂 Arşivlenmiş Karne Görüşleri (Düzenle)"])
        
        with tab_yukle:
            col_down, col_up = st.columns([1, 2])
            col_down.download_button("📄 Örnek Not Şablonu", data=eokul_sablon_olustur(), file_name="Eokul_Sablon.xlsx")
            k_dosya = col_up.file_uploader("E-Okul Not Listesini Yükle", type=['xlsx','csv'])

            if k_dosya and st.button("🚀 Listeyi Veritabanına Aktar"):
                try:
                    kdf = pd.read_csv(k_dosya, sep=None, engine='python') if k_dosya.name.endswith('.csv') else pd.read_excel(k_dosya)
                    cols = kdf.columns.tolist()
                    no_col = next((c for c in cols if "no" in str(c).lower()), cols[0])
                    ad_col = next((c for c in cols if "ad" in str(c).lower()), cols[1] if len(cols)>1 else cols[0])
                    sinif_col = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols)>2 else None)
                    not_cols = [c for c in cols if c not in [no_col, ad_col, sinif_col]]
                    
                    kdf.dropna(subset=[no_col], inplace=True)
                    db_karne_records = []
                    
                    # Veritabanına Karne Görevi olarak işleme
                    for _, row in kdf.iterrows():
                        o_no = str(row[no_col]).strip().replace('.0', '')
                        notlar_dict = {d: row[d] for d in not_cols if pd.notna(row.get(d))}
                        
                        # Eğer aynı dönem için kayıt varsa tekrar eklemesin diye kontrol
                        kontrol = df[(df['Okul'] == kb.get("okul")) & (df['Okul No'] == o_no) & (df['Gorev_Turu'] == 'Karne Gorusu')]
                        if kontrol.empty:
                            db_karne_records.append({
                                'okul': kb.get("okul"), 'ekleyen': aktif_id, 'atanan_ogretmen': aktif_id,
                                'ders': "Davranış / Karne", 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col],
                                'sinif': str(row[sinif_col]) if sinif_col else "Bilinmiyor", 
                                'gorev_turu': 'Karne Gorusu', 'gorev_adi': f"{time.strftime('%Y')} Dönem Sonu", 
                                'dinamik_json': {"notlar": notlar_dict},
                                'genel_degerlendirme_yorumu': "" # Başlangıçta boş
                            })
                    if db_karne_records:
                        supabase.table('gorevler').insert(db_karne_records).execute()
                        st.cache_data.clear()
                        st.success(f"✅ {len(db_karne_records)} öğrenci karne arşivine eklendi! Şimdi 'Arşivlenmiş Karne Görüşleri' sekmesinden AI ile görüş üretebilirsiniz.")
                        time.sleep(2); st.rerun()
                    else: st.warning("Bu öğrenciler zaten arşivde mevcut.")
                except Exception as e: st.error(f"Hata: {e}")
                
        with tab_liste:
            # Sadece Karne Görüşü olanları filtrele
            df_karne = df_yetkili[df_yetkili['Gorev_Turu'] == 'Karne Gorusu']
            if df_karne.empty:
                st.info("Sistemde arşivlenmiş karne görüşü bulunmuyor. Önce Excel yükleyiniz.")
            else:
                ogr_liste_k = df_karne.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist()
                secili_ogrenci_k = st.selectbox("🎯 İşlem Yapılacak Öğrenciyi Seçin", ["— Seçiniz —"] + ogr_liste_k)
                
                if secili_ogrenci_k != "— Seçiniz —":
                    o_no_k = secili_ogrenci_k.split(" - ")[0].strip()
                    satir_k = df_karne[df_karne['Okul No'] == o_no_k].iloc[0]
                    
                    st.markdown(f"#### 📊 {satir_k['Öğrenci Adı Soyadı']} — Not Profili")
                    eski_notlar = {}
                    try:
                        if pd.notna(satir_k.get('Dinamik_JSON', '')):
                            eski_notlar = json.loads(str(satir_k['Dinamik_JSON'])).get("notlar", {})
                    except: pass
                    
                    not_html = "<div style='display:flex;flex-wrap:wrap;gap:10px;margin-bottom:15px;'>"
                    for ders, notu in eski_notlar.items():
                        not_html += f"<div style='background:white;border:1px solid #bfdbfe;padding:8px 12px;border-radius:8px;'><strong style='color:#0d9488;'>{ders}:</strong> {notu}</div>"
                    not_html += "</div>"
                    st.markdown(not_html, unsafe_allow_html=True)
                    
                    c_a1, c_a2 = st.columns([1, 2])
                    obs = c_a1.text_area("Öğretmen Özel Gözlemi (Opsiyonel)", placeholder="Örn: Çok çalışkan...")
                    if c_a1.button("✨ AI Görüş Üret", use_container_width=True):
                        with st.spinner("Görüş yazılıyor..."):
                            try:
                                g_metin = ai_karne_gorusu_yaz(satir_k['Öğrenci Adı Soyadı'], satir_k['Sınıf'], eski_notlar, obs, kb["ad"])
                                # DB güncelle
                                supabase.table('gorevler').update({'genel_degerlendirme_yorumu': g_metin}).eq('okul_no', o_no_k).eq('gorev_turu', 'Karne Gorusu').execute()
                                st.cache_data.clear()
                                st.success("Görüş Üretildi!"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Hata: {e}")
                            
                    y_gorus = c_a2.text_area("Görüşü Düzenle / Onayla", value=satir_k.get('Genel Değerlendirme Yorumu', ''), height=180)
                    if c_a2.button("💾 Manuel Değişikliği Arşive Kaydet"):
                        supabase.table('gorevler').update({'genel_degerlendirme_yorumu': y_gorus}).eq('okul_no', o_no_k).eq('gorev_turu', 'Karne Gorusu').execute()
                        st.cache_data.clear()
                        st.success("Arşive kaydedildi!"); time.sleep(1); st.rerun()
                        
                st.markdown("---")
                out_k = io.BytesIO()
                with pd.ExcelWriter(out_k, engine='xlsxwriter') as writer:
                    df_karne[['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Genel Değerlendirme Yorumu']].to_excel(writer, index=False, sheet_name='Arsiv_Gorusleri')
                st.download_button("📥 Tüm Arşivlenmiş Görüşleri Excel İndir", data=out_k.getvalue(), file_name="E_Okul_Arsiv.xlsx")

        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKME: AYARLAR (Basitleştirilmiş)
    # ══════════════════════════════════════════════════
    elif aktif_ana == "ayarlar":
        st.markdown('<div class="glass-card"><div class="section-header">⚙️ Profil ve Ayarlar</div>', unsafe_allow_html=True)
        with st.form("profil_form"):
            p_ad     = st.text_input("Ad Soyad", value=kb["ad"])
            p_brans  = st.text_input("Branş", value=kb.get("brans",""))
            p_eposta = st.text_input("E-posta", value=kb.get("eposta",""))
            p_sifre  = st.text_input("Yeni Şifre (boş bırakırsan değişmez)", type="password")
            if st.form_submit_button("💾 Bilgilerimi Güncelle"):
                guncelleme = {"ad": p_ad, "brans": p_brans, "eposta": p_eposta}
                if p_sifre.strip(): guncelleme["sifre"] = p_sifre
                ayarlar["kullanicilar"][aktif_id].update(guncelleme)
                ayar_kaydet(ayarlar)
                st.session_state["kullanici_bilgi"] = ayarlar["kullanicilar"][aktif_id]
                st.success("✅ Güncellendi!")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 13. ANA ÇALIŞTIRMA
# ==========================================
def main():
    ayarlar = ayar_yukle()
    df      = veri_yukle()

    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🧭 PUSULA 360</div>
        <div class="hero-subtitle">Bütüncül Proje, Performans ve Karne Değerlendirme Platformu</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("giris_yapti", False):
        giris_ekrani(df, ayarlar)
    else:
        yonetim_paneli(df, ayarlar)

    st.markdown("""
    <div class="app-footer">
        <div style="font-weight:700;color:white;font-size:1rem;margin-bottom:6px;">🧭 PUSULA 360</div>
        <div>Proje, Performans ve Karne Yönetim Sistemi</div><br>
        <div>Sistem Tasarımcısı: <strong style="color:white;">Sıraç AKSAN</strong> &nbsp;|&nbsp; 📧 saracaksan@gmail.com</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
