import streamlit as st
import pandas as pd
import io
import os
import json
import requests
import time

# ==========================================
# 1. SAYFA YAPILANDIRMASI
# ==========================================
st.set_page_config(
    page_title="Dargeçit MEB | Gelişmiş Ölçme Değerlendirme Sistemi",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. GÜVENLİ API AYARLARI
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    GEMINI_API_KEY = "YOK" 

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# ==========================================
# 3. YÜKSEK KONTRASTLI MODERN CSS TASARIMI
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Inter:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f1f5f9; color: #0f172a; }
.hero-header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 16px; padding: 30px; text-align: center; box-shadow: 0 10px 25px rgba(30, 58, 138, 0.2); margin-bottom: 25px; border: 1px solid #93c5fd; }
.hero-title { font-family: 'Nunito', sans-serif; font-size: 2.4rem; font-weight: 900; color: #ffffff; margin: 0; text-shadow: 1px 2px 4px rgba(0,0,0,0.1); }
.hero-subtitle { font-size: 1.1rem; color: #e0f2fe; margin-top: 8px; font-weight: 600; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: #e2e8f0; border-radius: 10px; padding: 5px; gap: 5px; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: #ffffff; border-radius: 6px; color: #334155; font-weight: 700; padding: 10px 20px; border: 1px solid #cbd5e1; }
[data-testid="stTabs"] [aria-selected="true"] { background: linear-gradient(135deg, #f59e0b, #d97706) !important; color: white !important; border: none !important; box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3); }
.glass-card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { background-color: #f8fafc !important; border: 2px solid #94a3b8 !important; border-radius: 8px !important; color: #0f172a !important; font-weight: 600; font-size: 1rem !important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #2563eb !important; background-color: #ffffff !important; }
div[data-baseweb="select"] > div { background-color: #f8fafc !important; border: 2px solid #94a3b8 !important; color: #0f172a !important; font-weight: 600; border-radius: 8px !important; }
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label { color: #1e293b !important; font-weight: 800 !important; font-size: 0.95rem !important; }
.stButton > button { background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 800 !important; padding: 10px 20px !important; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important; }
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3) !important; }
.stDownloadButton > button { background: linear-gradient(135deg, #10b981, #059669) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SABİTLER, GÖMÜLÜ DARGEÇİT OKULLARI VE ŞABLONLAR
# ==========================================
CONFIG_FILE = "sistem_ayarlari.json"
DATA_FILE = "veritabani_v2.csv"

# Sisteme gömülü (hardcoded) Dargeçit okul listesi
DARGEÇIT_OKULLARI = [
    "Alayurt İlkokulu", "Alayurt Ortaokulu", "Altınoluk İlkokulu", "Altıyol İlkokulu",
    "Altıyol İmam Hatip Ortaokulu", "Anadolu Kız İmam Hatip Lisesi", "Atatürk Ortaokulu",
    "Bostanlı İlkokulu", "Cumhuriyet İlkokulu", "Dargeçit Anadolu İmam Hatip Lisesi",
    "Dargeçit Anadolu Lisesi", "Dargeçit Ilısu Anadolu Lisesi", "Dargeçit İmam Hatip Ortaokulu",
    "Dargeçit Yunus Emre İlkokulu", "Gazi Ortaokulu", "Ilısu İlkokulu", "Ilısu İlk-Ortaokulu",
    "Karabayır İlkokulu", "Karabayır İlkokulu İHO", "Kartalkaya İlkokulu", "Kılavuz İlkokulu",
    "Kılavuz Ortaokulu", "Nizamülmülk MTAL", "Sakarya İlkokulu", "Selahaddin Eyyubi İlkokulu",
    "Selahaddin Eyyubi İlkokulu/İHO", "Suçatı İlkokulu -", "Suçatı İlkokulu - İmam Hatip Ortaokulu",
    "Süleyman Altınkaynak Ortaokulu", "Sümer Beldesi İstiklal İlkokulu", "Sümer İlkokulu",
    "Sümer İmam Hatip Ortaokulu", "Tavşanlı İlk", "Tavşanlı İlk İHO", "Temelli İlkokulu",
    "Temelli İlkokulu/Ortaokulu", "Vatan İlkokulu", "Yılmaz İlkokulu", "Yoncalı İlkokulu",
    "Yoncalı İlkokulu-İmam Hatip Ortaokulu"
]

CEKIRDEK_SABLON = [
    { "id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi." },
    { "id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli hazırlanmış olması." },
    { "id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler." },
    { "id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyaller." },
    { "id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte teslim edilmesi." }
]

# Yeni Dinamik Yapı: Her satır spesifik bir değerlendirme görevine (Proje-1, Performans-2 vb.) aittir.
GEREKLI_SUTUNLAR = [
    'Okul', 'Ekleyen', 'Atanan_Ogretmen', 'Ders', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 
    'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON'
]

# ==========================================
# 5. DOSYA VE VERİ YÖNETİMİ
# ==========================================
def ayar_yukle():
    if not os.path.exists(CONFIG_FILE):
        varsayilan = {
            "okullar": DARGEÇIT_OKULLARI.copy(),
            "sablonlar": {"Gazi Matematik Şablonu": CEKIRDEK_SABLON},
            "kullanicilar": {
                "admin": {"sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi", "brans": "Tüm Dersler", "okul": "İlçe MEM"}
            },
            "sistem_kilitli": False
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(varsayilan, f, ensure_ascii=False, indent=4)
        return varsayilan
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "sablonlar" not in data: data["sablonlar"] = {"Gazi Matematik Şablonu": CEKIRDEK_SABLON}
        if "sistem_kilitli" not in data: data["sistem_kilitli"] = False
        if "okullar" not in data or not data["okullar"]: data["okullar"] = DARGEÇIT_OKULLARI.copy()
        return data

def ayar_kaydet(ayarlar):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(ayarlar, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=0)
def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype={"Okul No": str})
            df.dropna(subset=['Okul No'], inplace=True)
            df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
            
            for col in GEREKLI_SUTUNLAR:
                if col not in df.columns:
                    df[col] = "" if col not in ['Toplam Puan'] else None
            return df
        except Exception: 
            return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
    return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

def veriyi_kaydet(df):
    df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()

def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Yukleme_Listesi')
        worksheet = writer.sheets['Ogrenci_Yukleme_Listesi']
        for col_num, _ in enumerate(sablon_df.columns.values):
            worksheet.set_column(col_num, col_num, 25)
    return output.getvalue()

def eokul_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Matematik Notu', 'Türkçe Notu', 'Fen Bilimleri Notu'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='E_Okul_Karne_Listesi')
    return output.getvalue()

# ==========================================
# 6. YAPAY ZEKA BAĞLANTILARI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    if GEMINI_API_KEY == "YOK":
        raise Exception("API Anahtarı eksik! Lütfen Streamlit Secrets paneline ekleyin.")

    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye = "".join(filter(str.isdigit, sinif_str))
    seviye = seviye if seviye else "7" 
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])
    
    prompt = f"""Sen tecrübeli bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}.
Öğrenci {seviye}. Sınıfa gidiyor. Öğrenciyle doğrudan şefkatli bir 'sen' diliyle konuşacaksın.
Değerlendirme Kriterleri ve Maksimum Puanları şunlardır:
{kriter_ozeti}

GÖREV MODU: """

    if mod == "A":
        prompt += f"""YORUMDAN PUAN ÜRETME MODU. Öğretmenin notu: "{ham_metin}"
Görev: Öğretmenin bu notunu analiz et. Öğrencinin yaşına uygun her kritere ait alt açıklamaları yaz. Nottaki vurgulara göre her kriter için MANTIKLI BİR PUAN belirle."""
    elif mod == "B":
        prompt += f"""HEDEF PUANDAN YORUM ÜRETME MODU. Öğretmenin belirlediği Hedef Toplam Puan: {hedef_puan} / 100
Görev: Bu hedef toplam puana ulaşacak şekilde kriterlere mantıklı puanlar dağıt ve motivasyonel açıklamalar yaz."""
    else: 
        mevcut_puan_ozeti = "\n".join([f"  - {k['id']} Kriteri: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA MODU. Öğretmen puanları kendi girdi:
{mevcut_puan_ozeti}
Görev: Sadece verilen puanlara bakarak pedagojik ve motive edici açıklamalar yaz. Puanları KESİNLİKLE DEĞİŞTİRME."""

    prompt += f"""

"genel": Gelecek tavsiyelerini içeren genel bir yorum.
SADECE GEÇERLİ JSON FORMATINDA CEVAP VER. BAŞKA HİÇBİR METİN YAZMA:
{{
  "puanlar": {{ "{kriterler[0]['id']}": 40 }},
  "aciklamalar": {{ "{kriterler[0]['id']}": "Açıklama..." }},
  "genel": "Genel yorum..."
}}"""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    response.raise_for_status()
    raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw_text)

def ai_karne_gorusu_yaz(ogrenci_adi, sinifi, notlar_sozlugu, davranis_notu, ogrt_ad):
    if GEMINI_API_KEY == "YOK": raise Exception("API Anahtarı eksik!")
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu)])
    prompt = f"""Sınıf rehber öğretmeni {ogrt_ad} olarak {sinifi} sınıfından {ogrenci_adi} isimli öğrenciye dönem sonu karne görüşü yaz.
Ders Notları:\n{notlar_metni}\nGözlem: {davranis_notu}\nDoğrudan öğrenciye hitap eden 3-4 cümlelik şefkatli bir e-okul karne görüşü metni üret."""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ==========================================
# 7. CANLI VE DİNAMİK HTML REPORT OLUŞTURUCU
# ==========================================
def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = """<!DOCTYPE html>
    <html lang="tr"><head><meta charset="UTF-8"><title>Ölçme Değerlendirme Raporu</title>
    <style>
      body { font-family: 'Segoe UI', Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 20px; }
      .page { background: white; width: 210mm; margin: 0 auto 20px; padding: 15mm; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); page-break-after: always; border-top: 8px solid #2563eb; }
      table { width: 100%; border-collapse: collapse; margin-top: 20px; }
      th { background: #f8fafc; color: #1e293b; padding: 12px; text-align: left; font-size: 0.9rem; border-bottom: 2px solid #cbd5e1; }
      td { padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem; line-height: 1.6; color: #334155; }
      .header { background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 25px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; }
      .student-info { display: flex; gap: 20px; margin-top: 20px; padding: 15px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #3b82f6; }
      .info-item { display: flex; flex-direction: column; }
      .info-label { font-size: 0.75rem; color: #64748b; font-weight: bold; }
      .info-value { font-size: 1.05rem; font-weight: 800; color: #0f172a; }
      .yorum-kutu { background: #fffbeb; padding: 20px; margin-top: 25px; border-radius: 8px; border-left: 5px solid #f59e0b; color: #78350f; }
    </style></head><body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam = int(pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce')) if pd.notna(b.get('Toplam Puan', 0)) else 0
        dinamik_puanlar = json.loads(str(b.get('Dinamik_JSON', '{}'))) if pd.notna(b.get('Dinamik_JSON', '{}')) else {}
        
        html += f"""
        <div class="page">
          <div class="header">
            <div>
                <div style="font-weight:bold; text-transform:uppercase;">{b.get('Okul', '')}</div>
                <h1 style="margin: 5px 0 0; font-size:1.6rem;">{b.get('Gorev_Adi', 'Değerlendirme')} ({b.get('Ders', ogrt_brans)}) Raporu</h1>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.5rem; font-weight: 900; background: white; color: #2563eb; padding: 5px 25px; border-radius: 12px;">{toplam}</div>
                <div style="font-size: 0.8rem; margin-top: 5px; font-weight: bold;">ALINAN PUAN</div>
            </div>
          </div>
          
          <div class="student-info">
            <div class="info-item"><span class="info-label">Öğrenci Adı Soyadı</span><span class="info-value">{b.get('Öğrenci Adı Soyadı','')}</span></div>
            <div class="info-item"><span class="info-label">Sınıf</span><span class="info-value">{b.get('Sınıf','')}</span></div>
            <div class="info-item"><span class="info-label">Okul No</span><span class="info-value">{b.get('Okul No','')}</span></div>
            <div class="info-item"><span class="info-label">Görev Türü</span><span class="info-value">{b.get('Gorev_Turu','')}</span></div>
          </div>

          <table>
            <tr><th>Kriter</th><th style="text-align:center;">Maksimum</th><th style="text-align:center;">Alınan</th><th>Öğretmen Değerlendirmesi</th></tr>
        """
        for k in aktif_kriterler:
            p = dinamik_puanlar.get(f"{k['id']}_puan", 0)
            a = dinamik_puanlar.get(f"{k['id']}_aciklama", "Açıklama girilmedi.")
            html += f"<tr><td><strong>{k['baslik']}</strong></td><td style='text-align:center;'>{k['max']}</td><td style='text-align:center; font-weight:bold; color:#2563eb;'>{p}</td><td>{a}</td></tr>"
        
        html += f"""
          </table>
          <div class='yorum-kutu'><strong>💬 Değerlendirme Yorumu & Gelişim Tavsiyesi:</strong><br><br>{b.get('Genel Değerlendirme Yorumu', 'Geri bildirim yok.')}</div>
          <div style="text-align:right; margin-top:30px;"><strong>{ogrt_ad}</strong><br>{b.get('Ders', ogrt_brans)} Öğretmeni</div>
        </div>"""
    html += "</body></html>"
    return html

# ==========================================
# 8. ÖĞRENCİ PANELİ
# ==========================================
def ogrenci_paneli(df, ayarlar):
    st.markdown("<h2 style='text-align:center; color:#1e293b; font-weight:900;'>🎓 Öğrenci Proje & Performans Sorgulama</h2>", unsafe_allow_html=True)
    if df.empty: return st.warning("⚠️ Sistemde henüz ilan edilmiş performans/proje kaydı bulunmamaktadır.")

    col_m = st.columns([1, 2, 1])[1]
    with col_m:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        secili_okul = st.selectbox("🏫 Okulunuz", ["— Okul Seçiniz —"] + sorted(df['Okul'].unique().tolist()))
        siniflar = ["— Sınıf Seçiniz —"] + sorted(df[df['Okul'] == secili_okul]['Sınıf'].dropna().unique().tolist()) if secili_okul != "— Okul Seçiniz —" else []
        secili_sinif = st.selectbox("📚 Sınıfınız", siniflar if siniflar else ["Önce okul seçin"])
        okul_no = st.text_input("🔢 Okul Numaranız")
        sorgula = st.button("🔍 Değerlendirmelerimi Listele", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if sorgula and secili_okul != "— Okul Seçiniz —" and okul_no.strip():
        op = df[(df['Okul'] == secili_okul) & (df['Sınıf'] == secili_sinif) & (df['Okul No'] == okul_no.strip())]
        if op.empty:
            st.error("❌ Kayıt bulunamadı. Lütfen bilgilerinizi kontrol edin.")
        else:
            st.success(f"🎉 Hoş geldin, {op.iloc[0]['Öğrenci Adı Soyadı']}! Senin için tanımlanmış {len(op)} adet görev bulundu:")
            for idx, row in op.iterrows():
                with st.expander(f"📌 {row['Gorev_Adi']} - {row['Ders']} ({row['Gorev_Turu']}) — Puan: {row['Toplam Puan']}"):
                    tek_df = pd.DataFrame([row])
                    html_k = toplu_karne_html_dosyasi_uret(tek_df, "Ders Öğretmeni", row['Ders'], CEKIRDEK_SABLON)
                    st.components.v1.html(html_k, height=500, scrolling=True)

# ==========================================
# 9. YETKİLİ GİRİŞ & ÖĞRETMEN KAYIT PANELİ
# ==========================================
def giris_paneli(ayarlar):
    col_m = st.columns([1, 1.3, 1])[1]
    with col_m:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        g_sekme1, g_sekme2 = st.tabs(["🔐 Giriş Yap", "📝 Öğretmen Kayıt Ol"])
        
        with g_sekme1:
            if ayarlar.get("sistem_kilitli", False):
                st.error("🔒 Sistem idare kilitli modundadır. Sadece yöneticiler girebilir.")
            k_adi = st.text_input("Kullanıcı Adı", key="login_kadi")
            sifre = st.text_input("Şifre", type="password", key="login_sifre")
            
            if st.button("🚀 Giriş Yap", use_container_width=True):
                user = ayarlar["kullanicilar"].get(k_adi)
                if user and user["sifre"] == sifre:
                    if ayarlar.get("sistem_kilitli", False) and user["rol"] != "admin":
                        st.error("❌ Sistem öğretmen girişine kapalıdır.")
                    else:
                        st.session_state["giris_yapti"] = True
                        st.session_state["aktif_kullanici"] = k_adi
                        st.session_state["kullanici_bilgi"] = user
                        st.rerun()
                else: st.error("❌ Hatalı Giriş Verileri!")
                
        with g_sekme2:
            st.markdown("#### Yeni Öğretmen Hesabı Oluştur")
            reg_okul = st.selectbox("🏫 Görev Yaptığınız Okul", ayarlar["okullar"])
            reg_kadi = st.text_input("👤 Kullanıcı Adı (Benzersiz)")
            reg_ad = st.text_input("📛 Adınız Soyadınız")
            reg_brans = st.text_input("📚 Branşınız (Örn: Matematik)")
            reg_sifre = st.text_input("🔑 Giriş Şifresi", type="password")
            
            if st.button("💾 Kayıt İşlemini Tamamla", use_container_width=True):
                if not reg_kadi or not reg_sifre or not reg_ad:
                    st.error("❌ Lütfen alanları boş bırakmayın.")
                elif reg_kadi in ayarlar["kullanicilar"]:
                    st.error("❌ Bu kullanıcı adı kullanımda!")
                else:
                    ayarlar["kullanicilar"][reg_kadi] = {
                        "sifre": reg_sifre, "rol": "ogretmen", "ad": reg_ad, "okul": reg_okul, "brans": reg_brans
                    }
                    ayar_kaydet(ayarlar)
                    st.success("🎉 Başarıyla kayıt oldunuz! Giriş Yap sekmesinden sisteme bağlanabilirsiniz.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 10. ÖĞRETMEN & ADMİN ANA KONTROL PANELİ
# ==========================================
def yonetim_paneli(df, ayarlar):
    aktif_id = st.session_state["aktif_kullanici"]
    k_bilgi = st.session_state["kullanici_bilgi"]
    rol = k_bilgi["rol"]

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff, #dbeafe); padding: 15px; border-radius:12px; border:1px solid #bfdbfe; margin-bottom:20px;">
        <span style="font-weight:900; color:#1e3a8a; font-size:1.2rem;">👋 Hoş Geldiniz: {k_bilgi['ad']}</span> | 
        <span style="font-weight:700; color:#2563eb;">Okul/Yetki: {k_bilgi.get('okul','')} - { 'Süper Admin' if rol=='admin' else 'Öğretmen'} ({k_bilgi.get('brans','')})</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Sistemden Güvenli Çıkış"):
        st.session_state.clear()
        st.rerun()

    # Admin her veriyi, Öğretmen sadece kendi okulunu ve ilişkili öğrencileri yönetir
    if rol == "admin":
        df_yetkili = df
        sekmeler = st.tabs(["🏢 Sistem & Okul Kontrol", "📂 Öğrenci & Görev Havuzu", "🤖 Performans / Proje Değerlendir", "📊 Analiz & Çıktılar", "📝 Karne Görüşü Motoru"])
    else:
        df_yetkili = df[(df['Okul'] == k_bilgi.get("okul")) & ((df['Atanan_Ogretmen'] == aktif_id) | (df['Atanan_Ogretmen'] == 'admin'))]
        sekmeler = st.tabs(["📂 Öğrenci & Görev Havuzu", "🤖 Performans / Proje Değerlendir", "📊 Analiz & Çıktılar", "📝 Karne Görüşü Motoru"])

    # --- SEKME 1 (ADMİN): SİSTEM, ŞABLON VE OKUL DÜZENLEME ---
    if rol == "admin":
        with sekmeler[0]:
            st.markdown("### 🛠️ Süper Yetkili Sistem Ayarları")
            c_s1, c_s2, c_s3 = st.columns(3)
            
            with c_s1:
                st.markdown("#### 🏢 Dinamik Okul Listesi Yönetimi")
                y_okul = st.text_input("Yeni Okul İsmi Girin")
                if st.button("➕ Listeye Yeni Okul Ekle", use_container_width=True) and y_okul.strip():
                    if y_okul.strip() not in ayarlar["okullar"]:
                        ayarlar["okullar"].append(y_okul.strip())
                        ayar_kaydet(ayarlar)
                        st.success("Okul eklendi.")
                        st.rerun()
                
                sil_okul = st.selectbox("Sistemden Silinecek Okul", ["— Seçiniz —"] + ayarlar["okullar"])
                if st.button("🗑️ Seçilen Okulu Sil", use_container_width=True) and sil_okul != "— Seçiniz —":
                    ayarlar["okullar"].remove(sil_okul)
                    ayar_kaydet(ayarlar)
                    st.success("Okul silindi.")
                    st.rerun()
            
            with c_s2:
                st.markdown("#### 👨‍🏫 Kayıtlı Öğretmen Hesapları")
                ogretmenler = {k: v for k, v in ayarlar["kullanicilar"].items() if v.get("rol") == "ogretmen"}
                if ogretmenler:
                    sec_ogrt = st.selectbox("İşlem Yapılacak Öğretmen", list(ogretmenler.keys()), format_func=lambda x: f"{ogretmenler[x]['ad']} ({ogretmenler[x]['okul']})")
                    o_yeni_sifre = st.text_input("Yeni Şifre Belirle", value=ogretmenler[sec_ogrt]["sifre"])
                    
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button("🔄 Şifre Güncelle", use_container_width=True):
                        ayarlar["kullanicilar"][sec_ogrt]["sifre"] = o_yeni_sifre
                        ayar_kaydet(ayarlar)
                        st.success("Şifre Değiştirildi.")
                    if c_btn2.button("🗑️ Hesabı Sil", use_container_width=True):
                        del ayarlar["kullanicilar"][sec_ogrt]
                        ayar_kaydet(ayarlar)
                        st.success("Hesap kaldırıldı.")
                        st.rerun()
                else: st.info("Sistemde henüz kayıtlı öğretmen yok.")

            with c_s3:
                st.markdown("#### 🔒 Sistem Kilidi")
                kilit = ayarlar.get("sistem_kilitli", False)
                if st.button("🔓 Sistemi Herkese Aç" if kilit else "🔒 Sistemi Öğretmenlere Kapat", use_container_width=True):
                    ayarlar["sistem_kilitli"] = not kilit
                    ayar_kaydet(ayarlar)
                    st.rerun()

            st.markdown("---")
            st.markdown("#### 📊 Kriter Şablon Ayarları (Toplam 100 Puan Olmalıdır)")
            if "taslak_df" not in st.session_state:
                st.session_state["taslak_df"] = pd.DataFrame([{"Kriter Başlığı": "İçerik", "Maksimum Puan": 50, "Açıklama": "."}])
            
            s_adi_input = st.text_input("Yeni Şablon İsmi")
            ed_df = st.data_editor(st.session_state["taslak_df"], num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.button("💾 Değerlendirme Şablonunu Kaydet"):
                t_p = pd.to_numeric(ed_df["Maksimum Puan"], errors="coerce").sum()
                if t_p == 100 and s_adi_input.strip():
                    n_k = [{"id": f"k{i+1}", "baslik": str(r["Kriter Başlığı"]), "max": int(r["Maksimum Puan"]), "icon": "📌", "aciklama": str(r["Açıklama"])} for i, r in ed_df.iterrows()]
                    ayarlar["sablonlar"][s_adi_input.strip()] = n_k
                    ayar_kaydet(ayarlar)
                    st.success("Şablon listeye eklendi.")
                    st.rerun()
                else: st.error("Hata: Toplam puan 100 olmalı ve bir isim girilmelidir.")

    # --- SEKME 2: ÖĞRENCİ VE ÇOKLU GÖREV HAVUZU ---
    sekme_veri = sekmeler[1] if rol == "admin" else sekmeler[0]
    with sekme_veri:
        st.markdown("### 📂 Öğrenci Listesi ve Yeni Görev (Proje/Performans) Tanımlama")
        v_t1, v_t2, v_t3 = st.tabs(["📥 Excel / Liste Yükle", "➕ Tekil Öğrenci Kaydet", "🗑️ Öğrenci / Görev Verisi Sil"])
        
        with v_t1:
            h_okul = k_bilgi.get("okul") if rol != "admin" else st.selectbox("Yükleme Yapılacak Okul", ayarlar["okullar"], key="excel_okul")
            st.download_button("📄 Örnek Liste Şablonunu İndir", data=bos_sablon_olustur(), file_name="Ogrenci_Sablon.xlsx", use_container_width=True)
            
            st.markdown("#### Tanımlanacak Görev Detayları")
            g_tur = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"])
            g_isim = st.text_input("Görevin Adı (Örn: Matematik Denklemler Projesi, Hücre Modeli Performansı vb.)")
            
            excel_file = st.file_uploader("Öğrenci Excel Listesini Seçin", type=['xlsx'])
            if excel_file and g_isim.strip() and st.button("🚀 Listeyi ve Görevi Sisteme İşle", use_container_width=True):
                try:
                    excel_df = pd.read_excel(excel_file, dtype={"Okul No": str})
                    excel_df.dropna(subset=['Okul No'], inplace=True)
                    excel_df['Okul No'] = excel_df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
                    
                    eklenen_sayac = 0
                    for _, row in excel_df.iterrows():
                        o_no = row['Okul No']
                        # Çift Kayıt Engelleme: Aynı okulda, aynı numaraya, aynı görevi atanmış mı kontrolü
                        kontrol = df[(df['Okul'] == h_okul) & (df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_isim.strip())]
                        
                        if kontrol.empty:
                            yeni_satir = {c: None for c in GEREKLI_SUTUNLAR}
                            yeni_satir.update({
                                'Okul': h_okul, 'Ekleyen': aktif_id, 'Atanan_Ogretmen': aktif_id,
                                'Ders': k_bilgi.get("brans","Genel"), 'Okul No': o_no,
                                'Öğrenci Adı Soyadı': row['Öğrenci Adı Soyadı'], 'Sınıf': str(row['Sınıf']),
                                'Gorev_Turu': g_tur, 'Gorev_Adi': g_isim.strip(), 'Dinamik_JSON': "{}"
                            })
                            df.loc[len(df)] = yeni_satir
                            eklenen_sayac += 1
                            
                    veriyi_kaydet(df)
                    st.success(f"✅ İşlem Başarılı! {eklenen_sayac} öğrenciye ilgili görev başarıyla tanımlandı.")
                    st.rerun()
                except Exception as e: st.error(f"Excel Okuma Hatası: {e}")

        with v_t2:
            with st.form("manuel_ogr_form"):
                st.markdown("#### Manuel Tekil Görev Tanımlama")
                m_okul = k_bilgi.get("okul") if rol != "admin" else st.selectbox("Okul", ayarlar["okullar"])
                m_no = st.text_input("Öğrenci Okul No")
                m_ad = st.text_input("Öğrenci Adı Soyadı")
                m_sinif = st.text_input("Sınıfı (Örn: 7/A)")
                m_gtur = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans"])
                m_gadi = st.text_input("Görev Adı")
                
                if st.form_submit_button("💾 Görevi Öğrenciye Ekle"):
                    if m_no.strip() and m_ad.strip() and m_gadi.strip():
                        yeni_satir = {c: None for c in GEREKLI_SUTUNLAR}
                        yeni_satir.update({
                            'Okul': m_okul, 'Ekleyen': aktif_id, 'Atanan_Ogretmen': aktif_id,
                            'Ders': k_bilgi.get("brans","Genel"), 'Okul No': m_no.strip(),
                            'Öğrenci Adı Soyadı': m_ad.strip(), 'Sınıf': m_sinif.strip(),
                            'Gorev_Turu': m_gtur, 'Gorev_Adi': m_gadi.strip(), 'Dinamik_JSON': "{}"
                        })
                        df.loc[len(df)] = yeni_satir
                        veriyi_kaydet(df)
                        st.success("Öğrenci görevi başarıyla kaydedildi.")
                        st.rerun()

        with v_t3:
            st.markdown("#### Veri Temizleme Bölümü")
            if not df_yetkili.empty:
                s_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                silinecek = st.selectbox("Sistemden Kaldırılacak Kayıt", ["— Seçiniz —"] + s_liste)
                if silinecek != "— Seçiniz —" and st.button("🗑️ Seçilen Görevi/Öğrenciyi Sil", use_container_width=True):
                    p_part = silinecek.split(" | ")[1].strip()
                    n_part = silinecek.split(" - ")[0].strip()
                    df = df[~((df['Okul No'] == n_part) & (df['Gorev_Adi'] == p_part))]
                    veriyi_kaydet(df)
                    st.success("Kayıt sistemden silindi.")
                    st.rerun()

    # --- SEKME 3: YAPAY ZEKA DESTEKLİ PERFORMANS/PROJE DEĞERLENDİRME ---
    sekme_puan = sekmeler[2] if rol == "admin" else sekmeler[1]
    with sekme_puan:
        st.markdown("### 🤖 Kriter Bazlı Yapay Zeka Ölçme Sistemi")
        if df_yetkili.empty:
            st.warning("Değerlendirilecek öğrenci/görev havuzu boş.")
        else:
            p_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']} ({r['Ders']})", axis=1).tolist()
            sec_p = st.selectbox("🎯 Puanlama Yapılacak Öğrenci Görevi", ["— Seçiniz —"] + p_liste)
            
            s_isimler = list(ayarlar.get("sablonlar", {}).keys())
            sec_sablon_ismi = st.selectbox("📋 Değerlendirme Ölçeği (Şablon)", s_isimler)
            aktif_sablon = ayarlar["sablonlar"].get(sec_sablon_ismi, CEKIRDEK_SABLON)
            
            if sec_p != "— Seçiniz —":
                p_no = sec_p.split(" - ")[0].strip()
                g_adi_sec = sec_p.split(" | ")[1].split(" (")[0].strip()
                
                idx = df[(df['Okul No'] == p_no) & (df['Gorev_Adi'] == g_adi_sec)].index[0]
                bilgi = df.iloc[idx]
                
                # Form verilerini session state'e bağlama (Kayıpları önlemek için)
                if st.session_state.get("current_idx") != idx:
                    st.session_state["current_idx"] = idx
                    e_puanlar = json.loads(str(bilgi.get('Dinamik_JSON', '{}'))) if pd.notna(bilgi.get('Dinamik_JSON', '{}')) else {}
                    for k in aktif_sablon:
                        st.session_state[f"val_p_{k['id']}"] = int(e_puanlar.get(f"{k['id']}_puan", 0))
                        st.session_state[f"val_a_{k['id']}"] = str(e_puanlar.get(f"{k['id']}_aciklama", ""))
                    st.session_state["val_genel"] = str(bilgi.get('Genel Değerlendirme Yorumu', ""))

                ai_modu = st.radio("🤖 YAPAY ZEKA MODU SEÇİN:", ["A", "B", "C"], format_func=lambda x: {
                    "A": "MOD A: Ben Sadece Genel Yorum Yazarım, Puanları AI Dağıtır",
                    "B": "MOD B: Ben Sadece Hedef Toplam Puan Girerim, AI Her Şeyi Yazar",
                    "C": "MOD C: Puanları Kendim Veririm, AI Sadece Edebi/Pedagojik Cümleler Kurar"
                }[x], horizontal=True)
                
                ham_metin, hedef_puan = "", 100
                if ai_modu == "A": ham_metin = st.text_area("Öğrenci Çalışması Hakkındaki Kısa Yorumunuz:")
                elif ai_modu == "B": hedef_puan = st.number_input("Verilecek Toplam Puan", 0, 100, 85)
                
                if st.button("✨ Yapay Zeka Değerlendirmesini Başlat", use_container_width=True):
                    with st.spinner("Yapay Zeka Analiz Ediyor..."):
                        try:
                            m_p_d = {k['id']: st.session_state.get(f"val_p_{k['id']}", 0) for k in aktif_sablon}
                            res = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, m_p_d, k_bilgi.get("ad","Öğretmen"), bilgi['Ders'])
                            
                            for k in aktif_sablon:
                                if k['id'] in res.get("puanlar", {}): st.session_state[f"val_p_{k['id']}"] = int(res["puanlar"][k['id']])
                                if k['id'] in res.get("aciklamalar", {}): st.session_state[f"val_a_{k['id']}"] = res["aciklamalar"][k['id']]
                            if "genel" in res: st.session_state["val_genel"] = res["genel"]
                            st.success("Yayay zeka verileri hazırladı! Aşağıdaki kayıt alanından kontrol edip kaydedebilirsiniz.")
                        except Exception as e: st.error(f"Yapay Zeka Motor Hatası: {e}")
                
                st.markdown("#### 📝 İnceleme ve Düzenleme Alanı")
                with st.form("puan_kayit_form"):
                    toplam_hesaplanan = 0
                    for k in aktif_sablon:
                        c1, c2 = st.columns([1, 4])
                        p_v = c1.number_input(f"{k['baslik']} (Max: {k['max']})", 0, k['max'], key=f"val_p_{k['id']}")
                        a_v = c2.text_area(f"{k['baslik']} Kriter Açıklaması", key=f"val_a_{k['id']}", height=70)
                        toplam_hesaplanan += p_v
                    
                    g_v = st.text_area("💬 Genel Sonuç Raporu ve Öğrenciye Tavsiyeler", key="val_genel")
                    
                    st.markdown(f"### 📊 Toplam Skor: **{toplam_hesaplanan} / 100**")
                    if st.form_submit_button("💾 Değerlendirmeyi Resmi Veritabanına Kaydet"):
                        d_kayit = {}
                        for k in aktif_sablon:
                            d_kayit[f"{k['id']}_puan"] = st.session_state[f"val_p_{k['id']}"]
                            d_kayit[f"{k['id']}_aciklama"] = st.session_state[f"val_a_{k['id']}"]
                        
                        df.at[idx, 'Dinamik_JSON'] = json.dumps(d_kayit, ensure_ascii=False)
                        df.at[idx, 'Genel Değerlendirme Yorumu'] = g_v
                        df.at[idx, 'Toplam Puan'] = toplam_hesaplanan
                        veriyi_kaydet(df)
                        st.success("Öğrenci puanlaması sisteme işlendi!")

    # --- SEKME 4: PROFESYONEL RAPORLAR VE ÇIKTILAR ---
    sekme_rapor = sekmeler[3] if rol == "admin" else sekmeler[2]
    with sekme_rapor:
        st.markdown("### 📊 Çizelge ve Karne Çıktı Yönetimi")
        if df_yetkili.empty:
            st.info("Raporlanacak veri bulunmamaktadır.")
        else:
            r_sinif = st.selectbox("Sınıf Seçin", sorted(df_yetkili['Sınıf'].dropna().unique()))
            df_y = df_yetkili[df_yetkili['Sınıf'] == r_sinif]
            
            g_filtresi = st.selectbox("Görev Filtresi", ["Tümü"] + df_y['Gorev_Adi'].unique().tolist())
            if g_filtresi != "Tümü":
                df_y = df_y[df_y['Gorev_Adi'] == g_filtresi]
                
            st.dataframe(df_y[['Okul No', 'Öğrenci Adı Soyadı', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan']], use_container_width=True, hide_index=True)
            
            # Excel İdare Listesi Çıktısı
            out_idare = io.BytesIO()
            with pd.ExcelWriter(out_idare, engine='xlsxwriter') as writer:
                df_y[['Okul No', 'Öğrenci Adı Soyadı', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan']].to_excel(writer, index=False, sheet_name='Not_Cizelgesi')
            
            st.download_button("🏢 İdare İçin Resmi Excel Çizelgesi İndir", data=out_idare.getvalue(), file_name=f"{r_sinif}_Resmi_Not_Listesi.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
            
            # HTML/PDF Performans Karneleri Toplu Çıktı
            if st.button("🖨️ Velilere Gönderilecek Renkli Performans Belgelerini Üret", use_container_width=True):
                html_c = toplu_karne_html_dosyasi_uret(df_y, k_bilgi.get("ad","Öğretmen"), k_bilgi.get("brans",""), CEKIRDEK_SABLON)
                st.download_button("📥 Hazırlanan Belgeleri İndir (HTML/PDF)", data=html_c, file_name=f"{r_sinif}_Performans_Karneleri.html", mime="text/html", use_container_width=True)

    # --- SEKME 5: E-OKUL KARNE GÖRÜŞÜ MOTORU ---
    sekme_karne = sekmeler[4] if rol == "admin" else sekmeler[3]
    with sekme_karne:
        st.markdown("### 📝 Yapay Zeka E-Okul Karne Görüşü Sihirbazı")
        st.download_button("📄 Boş E-Okul Not Entegrasyon Şablonunu İndir", data=eokul_sablon_olustur(), file_name="E_Okul_Not_Sablonu.xlsx")
        
        k_dosya = st.file_uploader("Öğrenci Ders Notlarını İçeren Excel'i Yükleyin", type=['xlsx'])
        if k_dosya:
            if "k_df_state" not in st.session_state:
                st.session_state["k_df_state"] = pd.read_excel(k_dosya)
                if "AI_Karne_Gorusu" not in st.session_state["k_df_state"].columns:
                    st.session_state["k_df_state"]["AI_Karne_Gorusu"] = ""
            
            k_df = st.session_state["k_df_state"]
            cols = k_df.columns.tolist()
            
            # Sütun eşleştirme otomasyonu
            c_ad = next((c for c in cols if "ad" in str(c).lower()), cols[1])
            c_no = next((c for c in cols if "no" in str(c).lower()), cols[0])
            c_sinif = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols)>2 else cols[0])
            not_cols = [c for c in cols if c not in [c_ad, c_no, c_sinif, "AI_Karne_Gorusu"]]
            
            c_l, c_r = st.columns([1, 2])
            with c_l:
                o_sec = st.selectbox("Görüş Yazılacak Öğrenci", k_df[c_ad].tolist())
                o_idx = k_df[k_df[c_ad] == o_sec].index[0]
                o_row = k_df.loc[o_idx]
                
                obs = st.text_area("Öğretmen Davranış Gözlem Notu (Opsiyonel)")
                if st.button("✨ Karne Görüşü Üret", use_container_width=True):
                    with st.spinner("AI Cümleleri Tasarlıyor..."):
                        n_dict = {d: o_row[d] for d in not_cols}
                        gorus_metni = ai_karne_gorusu_yaz(o_row[c_ad], o_row[c_sinif], n_dict, obs, k_bilgi.get("ad","Öğretmen"))
                        st.session_state["k_df_state"].at[o_idx, "AI_Karne_Gorusu"] = gorus_metni
                        st.rerun()
            
            with c_r:
                g_yazilan = st.text_area("Düzenle / Onayla", value=k_df.at[o_idx, "AI_Karne_Gorusu"], height=160)
                if st.button("💾 Görüşü Tabloya İşle"):
                    st.session_state["k_df_state"].at[o_idx, "AI_Karne_Gorusu"] = g_yazilan
                    st.success("Görüş onaylandı.")
            
            st.markdown("---")
            st.dataframe(st.session_state["k_df_state"][[c_no, c_ad, "AI_Karne_Gorusu"]], use_container_width=True)
            
            out_k = io.BytesIO()
            with pd.ExcelWriter(out_k, engine='xlsxwriter') as writer:
                st.session_state["k_df_state"].to_excel(writer, index=False, sheet_name='Karne_Gorusleri')
            st.download_button("📥 E-Okul Hazır Excel Listesini İndir", data=out_k.getvalue(), file_name="E_Okul_Karne_Gorusleri_Hazir.xlsx", use_container_width=True)

# ==========================================
# 11. ANA ÇALIŞTIRMA MODÜLÜ
# ==========================================
def main():
    ayarlar, df = ayar_yukle(), veri_yukle()
    st.markdown('<div class="hero-header"><div class="hero-title">🏫 Dargeçit İlçe Milli Eğitim Müdürlüğü</div><div class="hero-subtitle">Proje, Performans Ödevi ve Ölçme Değerlendirme Havuz Sistemi</div></div>', unsafe_allow_html=True)
    
    t_main1, t_main2 = st.tabs(["🎓 Öğrenci Giriş Portalı", "👨‍🏫 Öğretmen & İdare Yönetim Masası"])
    with t_main1: 
        ogrenci_paneli(df, ayarlar)
    with t_main2:
        if not st.session_state.get("giris_yapti", False): 
            giris_paneli(ayarlar)
        else: 
            yonetim_paneli(df, ayarlar)

if __name__ == "__main__":
    main()
