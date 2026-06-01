import streamlit as st
import pandas as pd
import io
import os
import json
import requests
import time
from supabase import create_client, Client

# ==========================================
# 1. SAYFA YAPILANDIRMASI
# ==========================================
st.set_page_config(
    page_title="PRO-PER-KAR | Bütüncül Değerlendirme Portalı",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. GİZLİ KASA (SECRETS) VE API BAĞLANTILARI
# ==========================================
# 1. Gemini API Bağlantısı
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
except Exception:
    st.error("⚠️ HATA: GEMINI_API_KEY gizli kasada (secrets) bulunamadı!")
    st.stop()

# 2. Supabase Veritabanı Bağlantısı
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip()
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"⚠️ HATA: Supabase bilgileri gizli kasada bulunamadı veya yanlış! Detay: {e}")
    st.stop()

# (Kodunuzun geri kalanı buradan itibaren aynı şekilde devam edecek...)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Inter:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; }
.hero-header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 12px; padding: 25px; text-align: center; box-shadow: 0 8px 20px rgba(30, 58, 138, 0.15); margin-bottom: 20px; }
.hero-title { font-family: 'Nunito', sans-serif; font-size: 2.2rem; font-weight: 900; color: #ffffff; margin: 0; }
.hero-subtitle { font-size: 1.1rem; color: #e0f2fe; margin-top: 5px; font-weight: 600; }
.glass-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.section-header { color: #1e40af; font-weight: 800; font-size: 1.2rem; margin-bottom: 15px; border-bottom: 2px solid #bfdbfe; padding-bottom: 5px; }
.stButton > button { background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important; }
.stDownloadButton > button { background: linear-gradient(135deg, #059669, #10b981) !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: #e2e8f0; border-radius: 8px; padding: 4px; gap: 4px; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: #ffffff; border-radius: 6px; font-weight: 700; color: #475569; }
[data-testid="stTabs"] [aria-selected="true"] { background: #f59e0b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SABİTLER, OKULLAR VE GAZİ MATEMATİK ŞABLONU
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
    { "id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi ve konu hakimiyeti." },
    { "id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli bir şekilde hazırlanmış olması. Kağıt kullanımının özeni." },
    { "id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler veya açıklamalar eklenmesi." },
    { "id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyallerle desteklenmesi." },
    { "id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte teslim edilmesi." }
]

SABLON_ADI = "PROJE DEĞERLENDİRME ÖLÇEĞİ (Varsayılan)"
GEREKLI_SUTUNLAR = ['Okul', 'Ekleyen', 'Atanan_Ogretmen', 'Ders', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON']

# ==========================================
# 3. KALICI VERİTABANI YÖNETİMİ
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
            return data
        else:
            varsayilan = {
                "okullar": DARGEÇIT_OKULLARI.copy(), "sablonlar": {SABLON_ADI: CEKIRDEK_SABLON},
                "kullanicilar": {"admin": {"sifre": "Saracaksan.47", "rol": "admin", "ad": "Sistem Yöneticisi", "brans": "Tüm Dersler", "okul": "İlçe MEM", "onayli": True}},
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
    except Exception as e: st.error(f"Ayarlar kaydedilemedi: {e}")

@st.cache_data(ttl=0)
def veri_yukle():
    try:
        response = supabase.table('gorevler').select('*').execute()
        if not response.data: return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
        df = pd.DataFrame(response.data)
        df.rename(columns={
            'okul': 'Okul', 'ekleyen': 'Ekleyen', 'atanan_ogretmen': 'Atanan_Ogretmen', 'ders': 'Ders', 
            'okul_no': 'Okul No', 'ogrenci_adi_soyadi': 'Öğrenci Adı Soyadı', 'sinif': 'Sınıf', 
            'gorev_turu': 'Gorev_Turu', 'gorev_adi': 'Gorev_Adi', 'toplam_puan': 'Toplam Puan', 
            'genel_degerlendirme_yorumu': 'Genel Değerlendirme Yorumu', 'dinamik_json': 'Dinamik_JSON'
        }, inplace=True)
        if 'Dinamik_JSON' in df.columns:
            df['Dinamik_JSON'] = df['Dinamik_JSON'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
        return df
    except Exception as e:
        return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Listesi')
        writer.sheets['Ogrenci_Listesi'].set_column(0, 2, 25)
    return output.getvalue()

def eokul_sablon_olustur():
    sablon_df = pd.DataFrame(columns=[
        'Öğrenci No', 'Adı Soyadı', 'Sınıfı', 'TÜRKÇE', 'MATEMATİK', 'HAYAT BİLGİSİ', 'FEN BİLİMLERİ', 
        'SOSYAL BİLGİLER', 'İNGİLİZCE', 'DİN KÜLTÜRÜ VE AHLAK BİLGİSİ', 'GÖRSEL SANATLAR', 'MÜZİK', 
        'BEDEN EĞİTİMİ VE SPOR', 'Davranış Notu'
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='E_Okul_Karne_Listesi')
    return output.getvalue()

# ==========================================
# 4. YAPAY ZEKA BAĞLANTILARI
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye = "".join(filter(str.isdigit, sinif_str)) if "".join(filter(str.isdigit, sinif_str)) else "7" 
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])
    prompt = f"""Sen profesyonel bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}. Karşında {seviye}. Sınıfa giden bir öğrenci var. 
Öğrenciyle doğrudan 'sen' diliyle şefkatli ve motive edici konuş. Değerlendirme Kriterleri:
{kriter_ozeti}\nGÖREV MODU: """
    if mod == "A": prompt += f"""YORUMDAN PUAN ÜRETME. Öğretmenin notu: "{ham_metin}"\nGörev: Bu nota göre alt açıklamalar yaz ve her kriter için MANTIKLI BİR PUAN belirle."""
    elif mod == "B": prompt += f"""HEDEF PUANDAN YORUM ÜRETME. Hedef Puan: {hedef_puan} / 100\nGörev: Bu puana ulaşacak şekilde kriterlere mantıklı puanlar dağıt ve açıklamalar yaz."""
    else: 
        mevcut_puan_ozeti = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"""MANUEL PUANLAMA. Öğretmen puanları verdi:\n{mevcut_puan_ozeti}\nGörev: Sadece verilen puanlara bakarak pedagojik açıklamalar yaz. PUANLARI DEĞİŞTİRME."""
    prompt += f"""\nEKSTRA: "genel" anahtarına gelecek tavsiyelerini içeren genel bir sonuç yorumu yaz.\nSADECE JSON FORMATINDA CEVAP VER:
{{ "puanlar": {{ "{kriterler[0]['id']}": 40 }}, "aciklamalar": {{ "{kriterler[0]['id']}": "Açıklama..." }}, "genel": "Genel yorum..." }}"""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    response.raise_for_status()
    raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(raw_text.replace('```json', '').replace('```', '').strip())

def ai_karne_gorusu_yaz(ogrenci_adi, sinifi, notlar_sozlugu, davranis_notu, ogrt_ad):
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu)])
    prompt = f"""Sınıf öğretmeni {ogrt_ad} olarak {sinifi} sınıfından {ogrenci_adi} adlı öğrenciye e-okul karne görüşü yaz.
Ders Notları:\n{notlar_metni}\nGözlem: {davranis_notu}\nPedagojik, doğrudan öğrenciye hitap eden 3-4 cümlelik metin üret."""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

# ==========================================
# 6. DİNAMİK HTML RAPOR OLUŞTURUCU
# ==========================================
def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = """<!DOCTYPE html>
    <html lang="tr"><head><meta charset="UTF-8"><title>Değerlendirme Raporu</title>
    <style>
      body { font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; margin: 0; padding: 20px; }
      .page { background: white; width: 210mm; margin: 0 auto 20px; padding: 15mm; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); page-break-after: always; border-top: 8px solid #2563eb; }
      table { width: 100%; border-collapse: collapse; margin-top: 20px; }
      th { background: #f1f5f9; color: #1e293b; padding: 12px; text-align: left; font-size: 0.9rem; border-bottom: 2px solid #cbd5e1; }
      td { padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem; line-height: 1.5; color: #334155; }
      .header { background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
      .info-box { display: flex; gap: 20px; margin-top: 15px; padding: 15px; background: #eff6ff; border-radius: 8px; border-left: 4px solid #3b82f6; }
      .info-item { display: flex; flex-direction: column; }
      .info-label { font-size: 0.75rem; color: #64748b; font-weight: bold; }
      .info-value { font-size: 1.05rem; font-weight: 800; color: #0f172a; }
      .yorum-kutu { background: #fffbeb; padding: 15px; margin-top: 20px; border-radius: 8px; border-left: 5px solid #f59e0b; color: #78350f; font-size: 0.95rem; }
    </style></head><body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        toplam = int(pd.to_numeric(b.get('Toplam Puan', 0), errors='coerce')) if pd.notna(b.get('Toplam Puan', 0)) else 0
        dinamik_puanlar = json.loads(str(b.get('Dinamik_JSON', '{}'))) if pd.notna(b.get('Dinamik_JSON', '{}')) else {}
        
        html += f"""
        <div class="page">
          <div class="header">
            <div>
                <div style="font-weight:bold; opacity:0.9;">{b.get('Okul', '')}</div>
                <h1 style="margin: 5px 0 0; font-size:1.5rem;">{b.get('Gorev_Adi', 'Değerlendirme')} ({b.get('Ders', ogrt_brans)})</h1>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2.2rem; font-weight: 900; background: white; color: #2563eb; padding: 5px 20px; border-radius: 8px;">{toplam}</div>
                <div style="font-size: 0.75rem; margin-top: 5px; font-weight: bold;">PUAN</div>
            </div>
          </div>
          <div class="info-box">
            <div class="info-item"><span class="info-label">Öğrenci Adı Soyadı</span><span class="info-value">{b.get('Öğrenci Adı Soyadı','')}</span></div>
            <div class="info-item"><span class="info-label">Sınıf</span><span class="info-value">{b.get('Sınıf','')}</span></div>
            <div class="info-item"><span class="info-label">Okul No</span><span class="info-value">{b.get('Okul No','')}</span></div>
            <div class="info-item"><span class="info-label">Görev Türü</span><span class="info-value">{b.get('Gorev_Turu','')}</span></div>
          </div>
          <table><tr><th style="width:25%">Kriter</th><th style="text-align:center; width:10%">Maks</th><th style="text-align:center; width:10%">Alınan</th><th>Açıklama</th></tr>
        """
        for k in aktif_kriterler:
            p = dinamik_puanlar.get(f"{k['id']}_puan", 0)
            a = dinamik_puanlar.get(f"{k['id']}_aciklama", "-")
            html += f"<tr><td><strong>{k['baslik']}</strong></td><td style='text-align:center;'>{k['max']}</td><td style='text-align:center; font-weight:bold; color:#2563eb;'>{p}</td><td>{a}</td></tr>"
        
        html += f"""
          </table>
          <div class='yorum-kutu'><strong>💬 Genel Yorum:</strong><br><br>{b.get('Genel Değerlendirme Yorumu', 'Geri bildirim yok.')}</div>
          <div style="text-align:right; margin-top:30px; color:#475569;"><strong>{ogrt_ad}</strong><br>{b.get('Ders', ogrt_brans)} Öğretmeni</div>
        </div>"""
    html += "</body></html>"
    return html

# ==========================================
# 7. GİRİŞ VE KAYIT EKRANLARI
# ==========================================
def ana_giris_ekranlari(df, ayarlar):
    t_ogr, t_ogrt = st.tabs(["🎓 Öğrenci Sorgulama Paneli", "👨‍🏫 Öğretmen / İdare Girişi"])
    
    with t_ogr:
        col_m = st.columns([1, 2, 1])[1]
        with col_m:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<div class='section-header'>Performans ve Proje Sorgulama</div>", unsafe_allow_html=True)
            s_okul = st.selectbox("🏫 Okulunuz", ["— Okul Seçiniz —"] + sorted(df['Okul'].unique().tolist()))
            s_siniflar = ["— Sınıf Seçiniz —"] + sorted(df[df['Okul'] == s_okul]['Sınıf'].dropna().unique().tolist()) if s_okul != "— Okul Seçiniz —" else []
            s_sinif = st.selectbox("📚 Sınıfınız", s_siniflar if s_siniflar else ["Önce okul seçin"])
            s_no = st.text_input("🔢 Okul Numaranız")
            
            if st.button("🔍 Sonuçlarımı Getir", use_container_width=True) and s_okul != "— Okul Seçiniz —" and s_no.strip():
                sonuclar = df[(df['Okul'] == s_okul) & (df['Sınıf'] == s_sinif) & (df['Okul No'] == s_no.strip())]
                if sonuclar.empty:
                    st.error("Kayıt bulunamadı.")
                else:
                    st.success(f"Hoş geldin, {sonuclar.iloc[0]['Öğrenci Adı Soyadı']}! Sisteme kayıtlı {len(sonuclar)} görevin var:")
                    for _, row in sonuclar.iterrows():
                        with st.expander(f"📌 {row['Gorev_Adi']} ({row['Ders']}) — Puan: {row['Toplam Puan']}"):
                            html_k = toplu_karne_html_dosyasi_uret(pd.DataFrame([row]), row['Atanan_Ogretmen'], row['Ders'], CEKIRDEK_SABLON)
                            st.components.v1.html(html_k, height=400, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with t_ogrt:
        c_giris = st.columns([1, 1.5, 1])[1]
        with c_giris:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            g_sekme1, g_sekme2 = st.tabs(["🔐 Giriş Yap", "📝 Sisteme Kayıt Ol"])
            
            with g_sekme1:
                if ayarlar.get("sistem_kilitli", False):
                    st.warning("Sistem öğretmen girişine kapatılmıştır. Sadece yöneticiler girebilir.")
                k_adi = st.text_input("Kullanıcı Adı", key="l_kadi")
                sifre = st.text_input("Şifre", type="password", key="l_sifre")
                if st.button("Giriş", use_container_width=True):
                    user = ayarlar["kullanicilar"].get(k_adi)
                    if user and user["sifre"] == sifre:
                        if user.get("rol") != "admin" and not user.get("onayli", True):
                            st.warning("⏳ Hesabınız yönetici onayındadır. Lütfen onaylanmasını bekleyiniz.")
                        elif ayarlar.get("sistem_kilitli", False) and user.get("rol") != "admin":
                            st.error("Sistem Kilitli!")
                        else:
                            st.session_state["giris_yapti"] = True
                            st.session_state["aktif_kullanici"] = k_adi
                            st.session_state["kullanici_bilgi"] = user
                            st.rerun()
                    else: st.error("Hatalı Giriş!")
                    
            with g_sekme2:
                r_okul = st.selectbox("Görev Yaptığınız Okul", ayarlar["okullar"])
                r_ad = st.text_input("Ad Soyad")
                r_brans = st.text_input("Branş")
                r_kadi = st.text_input("Kullanıcı Adı Seçin")
                r_sifre = st.text_input("Şifre Belirleyin", type="password")
                if st.button("Kayıt Ol", use_container_width=True):
                    if r_kadi in ayarlar["kullanicilar"]:
                        st.error("Bu kullanıcı adı alınmış.")
                    elif r_kadi and r_sifre and r_ad:
                        is_auto = ayarlar.get("otomatik_onay", True)
                        ayarlar["kullanicilar"][r_kadi] = {"sifre": r_sifre, "rol": "ogretmen", "ad": r_ad, "okul": r_okul, "brans": r_brans, "onayli": is_auto}
                        ayar_kaydet(ayarlar)
                        if is_auto: st.success("Kayıt başarılı! Giriş sekmesinden giriş yapabilirsiniz.")
                        else: st.success("Kayıt başarılı! Hesabınız yönetici onayındadır. Onaylandıktan sonra giriş yapabilirsiniz.")
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 8. ÖĞRETMEN VE İDARE YÖNETİM MASASI
# ==========================================
def yonetim_paneli(df, ayarlar):
    aktif_id = st.session_state["aktif_kullanici"]
    kb = st.session_state["kullanici_bilgi"]
    rol = kb["rol"]

    st.markdown(f"""
    <div style="background: white; padding: 15px 25px; border-radius: 12px; display:flex; justify-content:space-between; align-items:center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid #2563eb;">
        <div>
            <div style="font-size: 1.3rem; font-weight: 900; color: #1e293b;">Hoş Geldiniz, {kb['ad']}</div>
            <div style="font-size: 0.95rem; color: #64748b; font-weight: 600;">{kb.get('okul','')} | {kb.get('brans','')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Çıkış Yap"):
        st.session_state.clear()
        st.rerun()

    df_yetkili = df if rol == "admin" else df[(df['Okul'] == kb.get("okul")) & ((df['Atanan_Ogretmen'] == aktif_id) | (df['Atanan_Ogretmen'] == 'admin'))]

    if rol == "admin":
        sekme_basliklari = ["👥 Öğrenci & Görev İşlemleri", "🤖 AI Değerlendirme", "📊 Raporlar", "📝 E-Okul Karne", "⚙️ Sistem & Kullanıcı Ayarları"]
    else:
        sekme_basliklari = ["👥 Öğrenci & Görev İşlemleri", "🤖 AI Değerlendirme", "📊 Raporlar", "📝 E-Okul Karne", "⚙️ Profil Ayarları"]

    sekmeler = st.tabs(sekme_basliklari)

    # --- SEKME 1: ÖĞRENCİ VE GÖREV YÖNETİMİ ---
    with sekmeler[0]:
        t1_excel, t2_manuel, t3_mevcut_sinif, t4_temizle = st.tabs(["📥 Yeni Liste Yükle (Excel)", "➕ Tekil Ekle", "🏫 Mevcut Sınıfa Görev Ata (Havuz)", "🗑️ Silme İşlemleri"])
        
        with t1_excel:
            st.markdown("#### 📥 Excel ile Toplu Görev Tanımla")
            h_okul = kb.get("okul") if rol != "admin" else st.selectbox("Okul Seçin", ayarlar["okullar"], key="ex_okul")
            
            hedef_ogrt_ex = aktif_id
            if rol == "admin":
                ogrt_listesi = {k: f"{v['ad']} ({v.get('brans','-')})" for k, v in ayarlar["kullanicilar"].items() if v.get("rol") == "ogretmen" and v.get("okul") == h_okul and v.get("onayli", True)}
                if ogrt_listesi:
                    hedef_ogrt_ex = st.selectbox("Atanacak Öğretmeni Seçin", ["admin"] + list(ogrt_listesi.keys()), format_func=lambda x: "Yönetici Üzerinde Kalsın" if x == "admin" else ogrt_listesi[x])
                else:
                    st.warning("Bu okulda kayıtlı/onaylı öğretmen yok. Görev yöneticiye atanacak.")
                    hedef_ogrt_ex = "admin"

            g_tur = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"])
            g_isim = st.text_input("Görevin Adı (Örn: Dönem Sonu Fen Projesi)")
            st.download_button("📄 Örnek Excel Şablonunu İndir", data=bos_sablon_olustur(), file_name="Ogrenci_Sablon.xlsx")
            uploaded_file = st.file_uploader("Öğrenci Listesini Yükle", type=['xlsx'])
            
            if st.button("🚀 Listeyi Yükle ve Görevleri Ata", use_container_width=True):
                if not uploaded_file: st.error("❌ Lütfen Excel dosyasını yükleyin!")
                elif not g_isim.strip(): st.error("❌ Lütfen 'Görevin Adı' kutucuğuna bir isim yazın!")
                else:
                    try:
                        excel_df = pd.read_excel(uploaded_file, dtype={"Okul No": str})
                        no_col = next((c for c in excel_df.columns if "no" in str(c).lower()), excel_df.columns[0])
                        ad_col = next((c for c in excel_df.columns if "ad" in str(c).lower()), excel_df.columns[1])
                        sinif_col = next((c for c in excel_df.columns if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), excel_df.columns[2] if len(excel_df.columns)>2 else "Bilinmiyor")

                        excel_df.dropna(subset=[no_col], inplace=True)
                        excel_df[no_col] = excel_df[no_col].astype(str).str.strip().str.replace('.0', '', regex=False)
                        
                        db_records = []
                        for _, row in excel_df.iterrows():
                            o_no = row[no_col]
                            kontrol = df[(df['Okul'] == h_okul) & (df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_isim.strip()) & (df['Atanan_Ogretmen'] == hedef_ogrt_ex)]
                            if kontrol.empty:
                                target_ders = kb.get("brans","Genel") if hedef_ogrt_ex == "admin" else ayarlar["kullanicilar"][hedef_ogrt_ex].get("brans", "Genel")
                                db_records.append({
                                    'okul': h_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': hedef_ogrt_ex,
                                    'ders': target_ders, 'okul_no': o_no, 'ogrenci_adi_soyadi': row[ad_col], 
                                    'sinif': str(row.get(sinif_col, 'Bilinmiyor')), 'gorev_turu': g_tur, 
                                    'gorev_adi': g_isim.strip(), 'dinamik_json': {}
                                })
                        if db_records:
                            supabase.table('gorevler').insert(db_records).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {len(db_records)} öğrenciye '{g_isim}' görevi tanımlandı!"); time.sleep(1); st.rerun()
                        else:
                            st.warning("Seçilen görev bu listedeki öğrencilere ilgili öğretmen için zaten atanmış.")
                    except Exception as e: st.error(f"Hata: {e}")

        with t2_manuel:
            st.markdown("#### ➕ Tekil Görev/Öğrenci Ekle")
            with st.form("tekil_ekle"):
                m_okul = kb.get("okul") if rol != "admin" else st.selectbox("Okul", ayarlar["okullar"])
                hedef_ogrt_man = aktif_id
                if rol == "admin":
                    ogrt_listesi_man = {k: f"{v['ad']} ({v.get('okul','-')})" for k, v in ayarlar["kullanicilar"].items() if v.get("rol") == "ogretmen" and v.get("onayli", True)}
                    hedef_ogrt_man = st.selectbox("Öğretmen Seç (Tüm Okullar)", ["admin"] + list(ogrt_listesi_man.keys()), format_func=lambda x: "Yönetici Üzerinde Kalsın" if x == "admin" else ogrt_listesi_man[x])

                m_no = st.text_input("Okul No")
                m_ad = st.text_input("Ad Soyad")
                m_sinif = st.text_input("Sınıf")
                m_gtur = st.selectbox("Görev Türü", ["Proje", "Performans"])
                m_gadi = st.text_input("Görev Adı")
                
                if st.form_submit_button("Öğrenciye Ata / Kaydet"):
                    if m_no and m_ad and m_gadi:
                        target_ders_man = kb.get("brans","") if hedef_ogrt_man == "admin" else ayarlar["kullanicilar"][hedef_ogrt_man].get("brans", "")
                        db_insert = {
                            'okul': m_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': hedef_ogrt_man, 
                            'ders': target_ders_man, 'okul_no': m_no.strip(), 'ogrenci_adi_soyadi': m_ad, 
                            'sinif': m_sinif, 'gorev_turu': m_gtur, 'gorev_adi': m_gadi, 'dinamik_json': {}
                        }
                        supabase.table('gorevler').insert(db_insert).execute()
                        st.cache_data.clear()
                        st.success("Veritabanına Eklendi."); time.sleep(1); st.rerun()

        # YEPYENİ ÖZELLİK: ORTAK HAVUZDAN SINIF ATAMA (MÜKERRER KAYIT ÖNLEYİCİ)
        with t3_mevcut_sinif:
            st.markdown("#### 🏫 Sistemdeki (Havuzdaki) Sınıflara Yeni Görev Ata")
            st.info("Okulunuzdaki diğer öğretmenlerin veya idarenin yüklediği sınıfları buradan seçip kendi dersiniz için yeni görev (proje/performans) atayabilirsiniz.")
            
            islem_okul = kb.get("okul") if rol != "admin" else st.selectbox("İşlem Yapılacak Okul", ayarlar["okullar"], key="havuz_okul")
            
            mevcut_siniflar = df[df['Okul'] == islem_okul]['Sınıf'].dropna().unique().tolist()
            if mevcut_siniflar:
                secilen_siniflar = st.multiselect("Görev Atanacak Sınıflar (Birden fazla seçebilirsiniz)", mevcut_siniflar)
                
                h_ogrt = aktif_id
                if rol == "admin":
                    ogrt_list_h = {k: f"{v['ad']} ({v.get('brans','-')})" for k, v in ayarlar["kullanicilar"].items() if v.get("rol") == "ogretmen" and v.get("okul") == islem_okul and v.get("onayli", True)}
                    if ogrt_list_h:
                        h_ogrt = st.selectbox("Görevi Veren Öğretmen", ["admin"] + list(ogrt_list_h.keys()), format_func=lambda x: "Yönetici Üzerinde Kalsın" if x == "admin" else ogrt_list_h[x])
                    else:
                        st.warning("Bu okulda öğretmen yok.")
                        h_ogrt = "admin"
                
                g_tur_h = st.selectbox("Görev Türü", ["Proje Ödevi", "Ders İçi Performans", "1. Performans", "2. Performans"], key="gth")
                g_isim_h = st.text_input("Görevin Adı (Örn: Matematik Dönem Projesi)", key="gih")
                
                if st.button("🚀 Seçili Sınıflara Görevi Ata", use_container_width=True):
                    if not secilen_siniflar or not g_isim_h.strip():
                        st.error("Lütfen sınıf seçimi yapın ve görev adını girin.")
                    else:
                        pool_students = df[(df['Okul'] == islem_okul) & (df['Sınıf'].isin(secilen_siniflar))].drop_duplicates(subset=['Okul No'])
                        db_records_h = []
                        for _, row in pool_students.iterrows():
                            o_no = row['Okul No']
                            kontrol = df[(df['Okul'] == islem_okul) & (df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_isim_h.strip()) & (df['Atanan_Ogretmen'] == h_ogrt)]
                            if kontrol.empty:
                                target_ders = kb.get("brans","Genel") if h_ogrt == "admin" else ayarlar["kullanicilar"][h_ogrt].get("brans", "Genel")
                                db_records_h.append({
                                    'okul': islem_okul, 'ekleyen': aktif_id, 'atanan_ogretmen': h_ogrt,
                                    'ders': target_ders, 'okul_no': o_no, 'ogrenci_adi_soyadi': row['Öğrenci Adı Soyadı'], 
                                    'sinif': row['Sınıf'], 'gorev_turu': g_tur_h, 
                                    'gorev_adi': g_isim_h.strip(), 'dinamik_json': {}
                                })
                        if db_records_h:
                            supabase.table('gorevler').insert(db_records_h).execute()
                            st.cache_data.clear()
                            st.success(f"✅ Seçilen sınıflardaki {len(db_records_h)} öğrenciye yeni görev atandı!"); time.sleep(1); st.rerun()
                        else:
                            st.warning("Seçilen görev bu sınıflardaki öğrencilere ilgili öğretmen için zaten atanmış.")
            else:
                st.info("Bu okula ait sistemde henüz hiçbir öğrenci kaydı bulunmuyor. Lütfen önce Excel ile yükleme yapın.")

        with t4_temizle:
            st.markdown("#### 🗑️ Veri Temizleme")
            if not df_yetkili.empty:
                s_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
                silinecek = st.selectbox("Silinecek Görevi Seç", ["— Seçiniz —"] + s_liste)
                if st.button("Seçili Kaydı Supabase'den Sil") and silinecek != "— Seçiniz —":
                    o_no, g_ad = silinecek.split(" - ")[0].strip(), silinecek.split(" | ")[1].strip()
                    supabase.table('gorevler').delete().eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                    st.cache_data.clear()
                    st.success("Kalıcı olarak silindi."); time.sleep(1); st.rerun()

    # --- SEKME 2: YAPAY ZEKA İLE DEĞERLENDİRME ---
    with sekmeler[1]:
        st.markdown("<div class='section-header'>Yapay Zeka Destekli Puanlama</div>", unsafe_allow_html=True)
        if df_yetkili.empty:
            st.warning("Değerlendirilecek görev bulunamadı.")
        else:
            c_sec1, c_sec2 = st.columns([2, 1])
            puan_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']} | {r['Gorev_Adi']}", axis=1).tolist()
            secili_gorev = c_sec1.selectbox("🎯 Öğrenci ve Görevi Seçin", ["— Seçiniz —"] + puan_liste)
            
            s_isimler = list(ayarlar.get("sablonlar", {}).keys())
            sec_sablon_ismi = c_sec2.selectbox("📋 Değerlendirme Şablonu", s_isimler)
            aktif_sablon = ayarlar["sablonlar"].get(sec_sablon_ismi, CEKIRDEK_SABLON)

            if secili_gorev != "— Seçiniz —":
                o_no, g_ad = secili_gorev.split(" - ")[0].strip(), secili_gorev.split(" | ")[1].strip()
                idx = df[(df['Okul No'] == o_no) & (df['Gorev_Adi'] == g_ad)].index[0]
                bilgi = df.iloc[idx]

                if st.session_state.get("aktif_idx") != idx:
                    st.session_state["aktif_idx"] = idx
                    e_puanlar = json.loads(str(bilgi.get('Dinamik_JSON', '{}'))) if pd.notna(bilgi.get('Dinamik_JSON', '{}')) else {}
                    for k in aktif_sablon:
                        st.session_state[f"vp_{k['id']}"] = int(e_puanlar.get(f"{k['id']}_puan", 0))
                        st.session_state[f"va_{k['id']}"] = str(e_puanlar.get(f"{k['id']}_aciklama", ""))
                    st.session_state["vg"] = str(bilgi.get('Genel Değerlendirme Yorumu', ""))

                st.markdown('<div class="glass-card" style="background:#f0f9ff; border:1px solid #bae6fd;">', unsafe_allow_html=True)
                ai_modu = st.radio("🤖 Yapay Zeka Görev Modu:", ["A", "B", "C"], format_func=lambda x: {"A": "MOD A: Sadece Not/Yorum Girin, Puanları AI Dağıtsın", "B": "MOD B: Hedef Puan Girin, AI Geri Kalanı Yapsın", "C": "MOD C: Manuel Puan Verin, AI Sadece Edebi Yorum Yapsın"}[x], horizontal=True)
                
                ham_metin, hedef_puan = "", 100
                if ai_modu == "A": ham_metin = st.text_area("Öğretmen Notunuz:")
                elif ai_modu == "B": hedef_puan = st.number_input("Hedef Puan", 0, 100, 85)
                
                if st.button("✨ Yapay Zekayı Çalıştır", use_container_width=True):
                    with st.spinner("Yapay Zeka Analiz Ediyor..."):
                        try:
                            m_p_d = {k['id']: st.session_state.get(f"vp_{k['id']}", 0) for k in aktif_sablon}
                            res = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, m_p_d, kb.get("ad",""), bilgi['Ders'])
                            for k in aktif_sablon:
                                if k['id'] in res.get("puanlar", {}): st.session_state[f"vp_{k['id']}"] = int(res["puanlar"][k['id']])
                                if k['id'] in res.get("aciklamalar", {}): st.session_state[f"va_{k['id']}"] = res["aciklamalar"][k['id']]
                            if "genel" in res: st.session_state["vg"] = res["genel"]
                            st.success("Değerlendirme hazır! Lütfen aşağıdaki formu kontrol edip kaydedin.")
                        except Exception as e: st.error(f"AI Hatası: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("#### 📝 Puanlama ve Onay Formu")
                with st.form("kayit_formu"):
                    toplam_h = 0
                    for k in aktif_sablon:
                        st.markdown(f"""
                        <div style='background-color:#f0f9ff; padding:12px; border-radius:8px; border-left: 5px solid #2563eb; margin-bottom:10px;'>
                            <strong style='color:#1e3a8a; font-size:1.1rem;'>{k.get('icon', '📌')} {k['baslik']} (Maksimum: {k['max']} Puan)</strong><br>
                            <span style='color:#475569; font-size:0.9rem;'><i>{k['aciklama']}</i></span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        cc1, cc2 = st.columns([1.5, 4])
                        pv = cc1.number_input(f"Verilen Puan (Max: {k['max']})", 0, k['max'], key=f"vp_{k['id']}")
                        av = cc2.text_area("Öğretmen Değerlendirmesi", key=f"va_{k['id']}", height=68)
                        toplam_h += pv
                        st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)
                        
                    gv = st.text_area("💬 Genel Yorum ve Gelecek Tavsiyeleri", key="vg", height=100)
                    st.markdown(f"**Hesaplanan Toplam Puan: {toplam_h} / 100**")
                    
                    if st.form_submit_button("💾 Supabase Veritabanına Kaydet"):
                        d_k_flat = {}
                        for k in aktif_sablon: 
                            d_k_flat.update({f"{k['id']}_puan": st.session_state[f"vp_{k['id']}"], f"{k['id']}_aciklama": st.session_state[f"va_{k['id']}"]})
                        
                        supabase.table('gorevler').update({
                            'dinamik_json': d_k_flat,
                            'genel_degerlendirme_yorumu': gv,
                            'toplam_puan': toplam_h
                        }).eq('okul_no', o_no).eq('gorev_adi', g_ad).execute()
                        st.cache_data.clear()
                        st.success("Başarıyla Kalıcı Veritabanına Kaydedildi!"); time.sleep(1); st.rerun()

    # --- SEKME 3: ÇIKTILAR VE RAPORLAR ---
    with sekmeler[2]:
        st.markdown("<div class='section-header'>Rapor ve Belge Çıktıları</div>", unsafe_allow_html=True)
        if not df_yetkili.empty:
            r_sinif = st.selectbox("Sınıf Seçin", sorted(df_yetkili['Sınıf'].dropna().unique()))
            df_y = df_yetkili[df_yetkili['Sınıf'] == r_sinif]
            g_filtre = st.selectbox("Görev Filtrele", ["Tümü"] + df_y['Gorev_Adi'].unique().tolist())
            if g_filtre != "Tümü": df_y = df_y[df_y['Gorev_Adi'] == g_filtre]
            
            st.dataframe(df_y[['Okul No', 'Öğrenci Adı Soyadı', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan']], use_container_width=True)
            
            c_rap1, c_rap2 = st.columns(2)
            out_xls = io.BytesIO()
            with pd.ExcelWriter(out_xls, engine='xlsxwriter') as writer: df_y[['Okul No', 'Öğrenci Adı Soyadı', 'Gorev_Turu', 'Gorev_Adi', 'Toplam Puan']].to_excel(writer, index=False, sheet_name='Cizelge')
            c_rap1.download_button("🏢 Excel Çizelgesi İndir", data=out_xls.getvalue(), file_name=f"{r_sinif}_Cizelge.xlsx", use_container_width=True)
            
            if c_rap2.button("🖨️ PDF/HTML Karneleri Üret", use_container_width=True):
                s_aktif = ayarlar["sablonlar"].get(list(ayarlar["sablonlar"].keys())[0], CEKIRDEK_SABLON)
                h_cikti = toplu_karne_html_dosyasi_uret(df_y, kb.get("ad",""), kb.get("brans",""), s_aktif)
                st.download_button("📥 Belgeleri İndir", data=h_cikti, file_name=f"{r_sinif}_Karneler.html", mime="text/html", use_container_width=True)

            st.markdown("---")
            st.markdown("#### 💾 Öğretmen Veri Yedekleme")
            if st.button("Kendi Öğrenci/Görev Verilerimi Yedekle (Excel)"):
                out_yedek = io.BytesIO()
                with pd.ExcelWriter(out_yedek, engine='xlsxwriter') as writer: 
                    df_yetkili.to_excel(writer, index=False, sheet_name='Verilerim')
                st.download_button("📥 Yedeği İndir", data=out_yedek.getvalue(), file_name=f"Yedek_Verilerim_{time.strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)

    # --- SEKME 4: E-OKUL KARNE GÖRÜŞÜ ---
    with sekmeler[3]:
        st.markdown("<div class='section-header'>Yapay Zeka Karne Görüşü Yazıcı</div>", unsafe_allow_html=True)
        st.download_button("📄 Örnek Not Şablonu", data=eokul_sablon_olustur(), file_name="Eokul_Sablon.xlsx")
        k_dosya = st.file_uploader("Öğrenci Not Listesini Yükle (CSV veya Excel)", type=['xlsx', 'csv', 'xls'])
        
        if k_dosya:
            if "kdf" not in st.session_state or st.session_state.get("last_uploaded_k_file") != k_dosya.name:
                try:
                    if k_dosya.name.endswith('.csv'): kdf = pd.read_csv(k_dosya, sep=None, engine='python')
                    else: kdf = pd.read_excel(k_dosya)
                    if "AI_Karne_Gorusu" not in kdf.columns: kdf["AI_Karne_Gorusu"] = ""
                    st.session_state["kdf"] = kdf
                    st.session_state["last_uploaded_k_file"] = k_dosya.name
                except Exception as e: st.error(f"Dosya okuma hatası: {e}")
            
        if "kdf" in st.session_state:
            kdf = st.session_state["kdf"]
            cols = kdf.columns.tolist()
            c_ad = next((c for c in cols if "ad" in str(c).lower()), cols[1] if len(cols)>1 else cols[0])
            c_sinif = next((c for c in cols if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), cols[2] if len(cols)>2 else cols[0])
            not_cols = [c for c in cols if c not in [c_ad, c_sinif, cols[0], "AI_Karne_Gorusu", "Davranış Notu"]]
            
            c_k1, c_k2 = st.columns([1, 2])
            o_sec_k = c_k1.selectbox("Öğrenci", kdf[c_ad].tolist())
            o_idx_k = kdf[kdf[c_ad] == o_sec_k].index[0]
            
            davranis_metni = ""
            if "Davranış Notu" in kdf.columns and pd.notna(kdf.loc[o_idx_k, "Davranış Notu"]): davranis_metni = str(kdf.loc[o_idx_k, "Davranış Notu"])
            obs = c_k1.text_area("Öğretmen Gözlemi (Opsiyonel)", value=davranis_metni)
            
            if c_k1.button("✨ Görüş Üret", use_container_width=True):
                with st.spinner("AI Cümleleri Tasarlıyor..."):
                    n_dict = {d: kdf.loc[o_idx_k, d] for d in not_cols}
                    g_metin = ai_karne_gorusu_yaz(kdf.loc[o_idx_k, c_ad], kdf.loc[o_idx_k, c_sinif], n_dict, obs, kb.get("ad",""))
                    st.session_state["kdf"].at[o_idx_k, "AI_Karne_Gorusu"] = g_metin
                    st.rerun()
                
            y_gorus = c_k2.text_area("Görüşü Düzenle/Onayla", value=kdf.at[o_idx_k, "AI_Karne_Gorusu"], height=130)
            if c_k2.button("💾 Kaydet"):
                st.session_state["kdf"].at[o_idx_k, "AI_Karne_Gorusu"] = y_gorus
                st.success("Onaylandı.")
            
            out_k = io.BytesIO()
            with pd.ExcelWriter(out_k, engine='xlsxwriter') as writer: st.session_state["kdf"].to_excel(writer, index=False, sheet_name='Karne_Gorusleri')
            st.download_button("📥 Tamamlanan Listeyi İndir", data=out_k.getvalue(), file_name="E_Okul_Gorusleri.xlsx", use_container_width=True)

    # --- SEKME 5: SİSTEM VE ŞABLON AYARLARI (ADMİN) / PROFİL AYARLARI (ÖĞRETMEN) ---
    with sekmeler[4]:
        if rol == "admin":
            st.markdown("<div class='section-header'>Sistem, Kullanıcılar ve Kriter Şablonları (Süper Yetkili)</div>", unsafe_allow_html=True)
            c_ay1, c_ay2 = st.columns(2)
            
            with c_ay1:
                st.markdown("#### ⏳ Onay Bekleyen Öğretmenler")
                
                # Yeni Eklenen: Otomatik Onay Toggle Düğmesi
                oto_onay_durum = ayarlar.get("otomatik_onay", True)
                if st.checkbox("Öğretmenler Kayıt Olunca Otomatik Onaylansın", value=oto_onay_durum):
                    if not oto_onay_durum: 
                        ayarlar["otomatik_onay"] = True
                        ayar_kaydet(ayarlar)
                        st.rerun()
                else:
                    if oto_onay_durum:
                        ayarlar["otomatik_onay"] = False
                        ayar_kaydet(ayarlar)
                        st.rerun()

                bekleyenler = {k: v for k, v in ayarlar["kullanicilar"].items() if not v.get("onayli", True)}
                if bekleyenler:
                    sec_bekleyen = st.selectbox("Onay Bekleyenler", list(bekleyenler.keys()), format_func=lambda x: f"{bekleyenler[x]['ad']} ({bekleyenler[x]['okul']})")
                    col_onay1, col_onay2 = st.columns(2)
                    if col_onay1.button("✅ Öğretmeni Onayla"):
                        ayarlar["kullanicilar"][sec_bekleyen]["onayli"] = True
                        ayar_kaydet(ayarlar); st.rerun()
                    if col_onay2.button("❌ Reddet / Sil"):
                        del ayarlar["kullanicilar"][sec_bekleyen]
                        ayar_kaydet(ayarlar); st.rerun()
                else:
                    st.info("Şu an onay bekleyen öğretmen hesabı bulunmuyor.")

                st.markdown("#### 👨‍🏫 Kayıtlı Öğretmenleri Yönet")
                ogrt = {k: v for k, v in ayarlar["kullanicilar"].items() if v.get("rol") == "ogretmen" and v.get("onayli", True)}
                if ogrt:
                    sec_o = st.selectbox("Düzenlenecek Öğretmen", list(ogrt.keys()), format_func=lambda x: f"{ogrt[x]['ad']} ({ogrt[x]['okul']})")
                    with st.form("ogrt_duzenle_form"):
                        y_ad = st.text_input("Ad Soyad", value=ogrt[sec_o]['ad'])
                        y_okul_idx = ayarlar["okullar"].index(ogrt[sec_o]['okul']) if ogrt[sec_o]['okul'] in ayarlar["okullar"] else 0
                        y_okul = st.selectbox("Okul", ayarlar["okullar"], index=y_okul_idx)
                        y_brans = st.text_input("Branş", value=ogrt[sec_o].get('brans', ''))
                        y_sifre = st.text_input("Şifre", value=ogrt[sec_o]['sifre'])
                        guncelle = st.form_submit_button("💾 Bilgileri Güncelle")
                        
                    if guncelle:
                        ayarlar["kullanicilar"][sec_o].update({"ad": y_ad, "okul": y_okul, "brans": y_brans, "sifre": y_sifre})
                        ayar_kaydet(ayarlar)
                        st.success("Öğretmen bilgileri güncellendi!"); time.sleep(1); st.rerun()
                        
                    if st.button("🗑️ Öğretmeni Sistemden Sil", key="del_ogrt"):
                        del ayarlar["kullanicilar"][sec_o]
                        ayar_kaydet(ayarlar); st.rerun()
                else:
                    st.info("Kayıtlı ve onaylı öğretmen bulunmuyor.")
                
                st.markdown("#### ➕ Yeni Öğretmen Ekle (Manuel)")
                with st.form("manuel_ogrt_ekle"):
                    e_kadi = st.text_input("Kullanıcı Adı (Giriş İçin)")
                    e_ad = st.text_input("Ad Soyad")
                    e_okul = st.selectbox("Okul", ayarlar["okullar"])
                    e_brans = st.text_input("Branş")
                    e_sifre = st.text_input("Şifre")
                    if st.form_submit_button("Öğretmeni Ekle ve Onayla"):
                        if e_kadi in ayarlar["kullanicilar"]:
                            st.error("Bu kullanıcı adı mevcut!")
                        elif e_kadi and e_sifre and e_ad:
                            ayarlar["kullanicilar"][e_kadi] = {"sifre": e_sifre, "rol": "ogretmen", "ad": e_ad, "okul": e_okul, "brans": e_brans, "onayli": True}
                            ayar_kaydet(ayarlar)
                            st.success("Öğretmen eklendi ve otomatik onaylandı!")
                            st.rerun()

                st.markdown("#### 💾 Sistem Yedeği Al")
                if st.button("Tüm Veritabanını İndir (Excel)"):
                    all_data = df
                    out_yedek = io.BytesIO()
                    with pd.ExcelWriter(out_yedek, engine='xlsxwriter') as writer: 
                        all_data.to_excel(writer, index=False, sheet_name='Sistem_Yedek')
                    st.download_button("📥 Yedeği Bilgisayara İndir", data=out_yedek.getvalue(), file_name=f"Sistem_Yedek_{time.strftime('%Y%m%d')}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)

            with c_ay2:
                st.markdown("#### 🏢 Okul Listesi Yönetimi")
                y_okul_ekle = st.text_input("Yeni Okul Ekle")
                if st.button("Okulu Listeye Ekle") and y_okul_ekle:
                    ayarlar["okullar"].append(y_okul_ekle)
                    ayar_kaydet(ayarlar); st.rerun()
                
                sil_okul = st.selectbox("Okul Sil", ["— Seçiniz —"] + ayarlar["okullar"])
                if st.button("Seçili Okulu Sil") and sil_okul != "— Seçiniz —":
                    ayarlar["okullar"].remove(sil_okul)
                    ayar_kaydet(ayarlar); st.rerun()

                st.markdown("#### 📐 Yeni Şablon Tasarlayıcı")
                st.info("Önemli: Kriterlerin toplamı 100 puan olmalıdır.")
                if "t_df" not in st.session_state: st.session_state["t_df"] = pd.DataFrame([{"Başlık": "İçerik", "Puan": 50, "Açıklama": ""}])
                
                s_isim_yeni = st.text_input("Şablon Adı")
                e_df = st.data_editor(st.session_state["t_df"], num_rows="dynamic", use_container_width=True)
                
                if st.button("💾 Şablonu Kaydet"):
                    if pd.to_numeric(e_df["Puan"], errors="coerce").sum() == 100 and s_isim_yeni:
                        n_k = [{"id": f"k{i+1}", "baslik": str(r["Başlık"]), "max": int(r["Puan"]), "icon": "📌", "aciklama": str(r["Açıklama"])} for i, r in e_df.iterrows()]
                        ayarlar["sablonlar"][s_isim_yeni] = n_k
                        ayar_kaydet(ayarlar); st.success("Eklendi"); st.rerun()
                    else: st.error("Toplam 100 olmalı ve isim girilmeli.")

                st.markdown("#### Mevcut Şablonu Sil")
                sil_sablon = st.selectbox("Silinecek Şablonu Seç", list(ayarlar["sablonlar"].keys()))
                if st.button("🗑️ Şablonu Sil"):
                    if "Varsayılan" in sil_sablon: st.error("Ana varsayılan şablon silinemez!")
                    else: del ayarlar["sablonlar"][sil_sablon]; ayar_kaydet(ayarlar); st.rerun()
                    
        else: # SADECE ÖĞRETMEN PROFİL AYARLARI
            st.markdown("<div class='section-header'>Kişisel Profil Ayarları</div>", unsafe_allow_html=True)
            o_yeni_sifre = st.text_input("Yeni Şifreniz", value=kb["sifre"], type="password")
            o_yeni_ad = st.text_input("Ad Soyad", value=kb["ad"])
            o_yeni_brans = st.text_input("Branş", value=kb.get("brans", ""))
            if st.button("💾 Bilgilerimi Güncelle", use_container_width=True):
                ayarlar["kullanicilar"][aktif_id].update({"sifre": o_yeni_sifre, "ad": o_yeni_ad, "brans": o_yeni_brans})
                ayar_kaydet(ayarlar)
                st.session_state["kullanici_bilgi"] = ayarlar["kullanicilar"][aktif_id]
                st.success("Profiliniz başarıyla güncellendi!")

# ==========================================
# 8. ANA ÇALIŞTIRMA MODÜLÜ
# ==========================================
def main():
    ayarlar, df = ayar_yukle(), veri_yukle()
    st.markdown('<div class="hero-header"><div class="hero-title">🏫 PUSULA 360 Bütüncül Değerlendirme Platformu</div><div class="hero-subtitle">Proje, Performans ve Karne Yönetimi</div></div>', unsafe_allow_html=True)
    
    if not st.session_state.get("giris_yapti", False): 
        ana_giris_ekranlari(df, ayarlar)
    else: 
        yonetim_paneli(df, ayarlar)

if __name__ == "__main__":
    main()
