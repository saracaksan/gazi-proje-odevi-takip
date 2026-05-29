import streamlit as st
import pandas as pd
import io
import os
import json
import requests
import time

# ==========================================
# BÖLÜM 1: SİSTEM AYARLARI VE DOSYA YÖNETİMİ
# ==========================================
st.set_page_config(
    page_title="Gazi Ortaokulu | Proje Değerlendirme Sistemi",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# KENDİ DOĞRU API ANAHTARINIZ ("AIza" İLE BAŞLAYAN) EKLENDİ
GEMINI_API_KEY = "AIzaSyCxmD5HwVJTFoYEuCpGcGIUy04CLQ6dajE"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&family=Inter:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f1f5f9; color: #0f172a; }
.hero-header { background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%); border-radius: 16px; padding: 30px; text-align: center; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2); margin-bottom: 25px; border: 1px solid #bfdbfe; }
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

CONFIG_FILE = "sistem_ayarlari.json"
DATA_FILE = "veritabani.csv"

CEKIRDEK_SABLON = [
  { "id": "k1", "baslik": "İçerik ve Bilgi Doğruluğu", "max": 40, "icon": "📚", "aciklama": "Soruların doğru çözülmesi, işlem basamaklarının net gösterilmesi." },
  { "id": "k2", "baslik": "Düzen ve Tertip", "max": 15, "icon": "📐", "aciklama": "Ödevin temiz, okunaklı ve düzenli hazırlanmış olması." },
  { "id": "k3", "baslik": "Araştırma ve Zenginleştirme", "max": 15, "icon": "🔍", "aciklama": "Verilen sorular dışında konuyu destekleyen ekstra örnekler." },
  { "id": "k4", "baslik": "Yaratıcılık ve Sunum", "max": 15, "icon": "🎨", "aciklama": "Kapak tasarımı, renk kullanımı ve görsel materyaller." },
  { "id": "k5", "baslik": "Zamanında Teslim", "max": 15, "icon": "⏰", "aciklama": "Projenin belirtilen tarihte teslim edilmesi." }
]

GEREKLI_SUTUNLAR = ['Okul', 'Ekleyen', 'Ders', 'S.No', 'Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', '1. Dönem Puanı', 'Proje', 'Durum', 'Toplam Puan', 'Genel Değerlendirme Yorumu', 'Dinamik_JSON']
for _k in CEKIRDEK_SABLON: GEREKLI_SUTUNLAR.extend([f"{_k['baslik']} Puanı", f"{_k['baslik']} Açıklaması"])

def ayar_yukle():
    if not os.path.exists(CONFIG_FILE):
        varsayilan = {"okullar": ["Gazi Ortaokulu"], "sablonlar": {"Gazi Matematik Şablonu": CEKIRDEK_SABLON}, "kullanicilar": {"admin": {"sifre": "Sarac.47", "rol": "admin", "ad": "Sistem Yöneticisi", "brans": "Tüm Dersler"}}}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(varsayilan, f, ensure_ascii=False, indent=4)
        return varsayilan
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "sablonlar" not in data: data["sablonlar"] = {"Gazi Matematik Şablonu": CEKIRDEK_SABLON}
        return data

def ayar_kaydet(ayarlar):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(ayarlar, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=0)
def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype={"Okul No": str})
            df.dropna(subset=['Okul No'], inplace=True)
            df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
            for col in ['Okul', 'Ekleyen', 'Ders', 'Dinamik_JSON']:
                if col not in df.columns: df[col] = "Gazi Ortaokulu" if col == 'Okul' else ("admin" if col == 'Ekleyen' else ("Matematik" if col == 'Ders' else "{}"))
            for s in GEREKLI_SUTUNLAR:
                if s not in df.columns: df[s] = None
            for c in df.columns:
                if "Açıklaması" in c or "Yorumu" in c or "JSON" in c or c in ["Ders", "Öğrenci Adı Soyadı"]: df[c] = df[c].astype('object')
            return df
        except Exception: return pd.DataFrame(columns=GEREKLI_SUTUNLAR)
    return pd.DataFrame(columns=GEREKLI_SUTUNLAR)

def veriyi_kaydet(df):
    df['Okul No'] = df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()

def bos_sablon_olustur():
    sablon_df = pd.DataFrame(columns=['Okul No', 'Öğrenci Adı Soyadı', 'Sınıf', 'Ders', '1. Dönem Puanı', 'Proje', 'Durum'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sablon_df.to_excel(writer, index=False, sheet_name='Ogrenci_Sablonu')
        for col_num, _ in enumerate(sablon_df.columns.values): writer.sheets['Ogrenci_Sablonu'].set_column(col_num, col_num, 20)
    return output.getvalue()


# ==========================================
# BÖLÜM 2: ZIRHLI YAPAY ZEKA MOTORLARI VE HTML
# ==========================================
def ai_degerlendirme_yap(bilgi_dict, kriterler, mod, ham_metin, hedef_puan, manuel_puanlar, ogrt_ad, ogrt_brans):
    sinif_str = str(bilgi_dict.get("Sınıf", "7"))
    seviye = "".join(filter(str.isdigit, sinif_str))
    seviye = seviye if seviye else "7" 
    kriter_ozeti = "\n".join([f"  - {k['id']}: {k['baslik']} (Max: {k['max']} Puan)" for k in kriterler])
    
    prompt = f"""Sen tecrübeli bir {ogrt_brans} öğretmenisin. Adın {ogrt_ad}.
Karşında {seviye}. Sınıfa giden {int(seviye)+5} yaşında öğrenci var. Şefkatli, motive edici 'sen' dili kullan.
Kriterler:
{kriter_ozeti}

MOD: """

    if mod == "A": prompt += f"YORUMDAN PUAN ÜRET. Öğretmen notu: '{ham_metin}'. Öğretmenin notunu analiz et, kriterlere puan dağıt ve yaşa uygun açıkla."
    elif mod == "B": prompt += f"HEDEF PUANDAN ÜRET. Hedef Toplam Puan: {hedef_puan}/100. Bu puana ulaşacak şekilde mantıklı puan dağıt ve motive edici açıkla."
    else: 
        m_puan = "\n".join([f"  - {k['id']}: {manuel_puanlar.get(k['id'], 0)}/{k['max']}" for k in kriterler])
        prompt += f"MANUEL PUANLAMA. Öğretmen puanları: {m_puan}. Ek not: '{ham_metin}'. PUANLARI DEĞİŞTİRME, sadece puanlara uygun pedagojik açıklamalar yaz."

    prompt += f"""
EKSTRA: "genel" başlığıyla dersin hayatındaki önemini anlatan yorum yaz.
DİKKAT SADECE GEÇERLİ JSON ÜRET:
{{ "puanlar": {{ "{kriterler[0]['id']}": 40 }}, "aciklamalar": {{ "{kriterler[0]['id']}": "Açıklama..." }}, "genel": "Genel yorum..." }}"""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    try:
        response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
        response.raise_for_status()
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw_text = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        if "429" in str(e): raise Exception("Google API Kotası Doldu! Lütfen 1-2 dakika bekleyip tekrar deneyin.")
        else: raise Exception(f"Google AI Hatası: {e}")

def ai_karne_gorusu_yaz(ogrenci_adi, sinifi, notlar_sozlugu, davranis_notu, ogrt_ad):
    seviye_str = "".join(filter(str.isdigit, str(sinifi)))
    seviye = int(seviye_str) if seviye_str else 4
    notlar_metni = "\n".join([f"- {ders}: {notu}" for ders, notu in notlar_sozlugu.items() if pd.notna(notu) and str(notu).strip() != ""])

    prompt = f"""Sınıf rehber öğretmenisin. Adın {ogrt_ad}.
Karşında {sinifi} sınıfından ({seviye+5} yaşında) {ogrenci_adi} var. Dönem sonu karnesini veriyorsun. 'Sen' diliyle, pedagojik, bilimsel ve yaşına uygun görüş yaz.
Öğrencinin Notları:
{notlar_metni}
Öğretmen Gözlemi: "{davranis_notu if davranis_notu else 'Akademik çaba gösteriyor.'}"
Görev:
1. Yüksek notları överek takdir et.
2. Düşük notları kırmadan "planlı çalışırsak toparlarız" şeklinde yol göster.
3. Gözlemi sosyal gelişimini destekleyecek şekilde yedir.
4. Toplam 3-4 cümlelik, karneye yapıştırılabilecek metin olsun. SADECE METNİ YAZ."""

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "text/plain"}}
    try:
        response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=45)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        if "429" in str(e): raise Exception("Google API Kotası Doldu! Lütfen 1 dakika bekleyip butona tekrar basın.")
        else: raise Exception(f"Google AI Hatası: {e}")

def toplu_karne_html_dosyasi_uret(df_sinif, ogrt_ad, ogrt_brans, aktif_kriterler):
    html = f"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Karneler</title><style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #f1f5f9; padding: 20px; }}
  .page {{ background: white; width: 210mm; margin: 0 auto 20px; padding: 15mm; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); page-break-after: always; border-top: 8px solid #3b82f6; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
  th {{ background: #f8fafc; color: #1e293b; padding: 12px; text-align: left; font-size: 0.9rem; border-bottom: 2px solid #cbd5e1; text-transform: uppercase; }}
  td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem; vertical-align: top; line-height: 1.6; color: #334155; }}
  .header {{ background: linear-gradient(135deg, #2563eb, #38bdf8); color: white; padding: 25px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; }}
  .student-info {{ display: flex; gap: 20px; margin-top: 20px; padding: 15px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #38bdf8; }}
  .info-item {{ display: flex; flex-direction: column; }}
  .info-label {{ font-size: 0.75rem; color: #64748b; font-weight: bold; text-transform: uppercase; }}
  .info-value {{ font-size: 1.05rem; font-weight: 800; color: #0f172a; }}
  .yorum-kutu {{ background: #fffbeb; padding: 20px; margin-top: 25px; border-radius: 8px; border-left: 5px solid #f59e0b; line-height: 1.7; color: #78350f; font-size: 0.95rem; }}
  .imza {{ text-align: right; margin-top: 40px; color: #475569; font-size: 1rem; }}
  @media print {{ body {{ background: white; padding: 0; }} .page {{ box-shadow: none; margin: 0; border-top: none; }} .header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style></head><body>"""

    for i in range(len(df_sinif)):
        b = df_sinif.iloc[i]
        top_raw = b.get('Toplam Puan', 0)
        toplam = int(pd.to_numeric(top_raw, errors='coerce')) if pd.notna(top_raw) else 0
        renk = "#10b981" if toplam >= 85 else ("#f59e0b" if toplam >= 60 else "#ef4444")
        dinamik_puanlar = {}
        try:
            if str(b.get('Dinamik_JSON', '{}')).strip() not in ["nan", ""]: dinamik_puanlar = json.loads(b.get('Dinamik_JSON', '{}'))
        except: pass

        html += f"""<div class="page"><div class="header"><div><div style="font-size:0.9rem; font-weight:bold;">{b.get('Okul', 'Okul')}</div><h1 style="margin: 5px 0 0; font-size:1.8rem;">{b.get('Ders', ogrt_brans)} Proje Raporu</h1></div>
    <div style="text-align: center;"><div style="font-size: 2.8rem; font-weight: 900; background: white; color: {renk}; padding: 5px 30px; border-radius: 12px;">{toplam}</div><div style="font-size: 0.8rem; margin-top: 8px; font-weight: bold;">TOPLAM PUAN</div></div></div>
  <div class="student-info"><div class="info-item"><span class="info-label">Öğrenci</span><span class="info-value">{b.get('Öğrenci Adı Soyadı','')}</span></div><div class="info-item"><span class="info-label">Sınıf</span><span class="info-value">{b.get('Sınıf','')}</span></div><div class="info-item"><span class="info-label">Okul No</span><span class="info-value">{b.get('Okul No','')}</span></div></div>
  <table><tr><th style="width:25%;">Kriter</th><th style="width:10%; text-align:center;">Max</th><th style="width:10%; text-align:center;">Puan</th><th style="width:55%;">Değerlendirme</th></tr>"""
        for k in aktif_kriterler:
            p = int(pd.to_numeric(dinamik_puanlar.get(f"{k['id']}_puan", b.get(f"{k['baslik']} Puanı", 0)), errors='coerce')) if pd.notna(dinamik_puanlar.get(f"{k['id']}_puan", b.get(f"{k['baslik']} Puanı", 0))) else 0
            a = dinamik_puanlar.get(f"{k['id']}_aciklama", b.get(f"{k['baslik']} Açıklaması", "-"))
            if pd.isna(a) or str(a).strip() in ["", "nan"]: a = "Değerlendirme girilmedi."
            p_renk = "#10b981" if (p/k['max']) >= 0.8 else ("#f59e0b" if (p/k['max']) >= 0.5 else "#ef4444")
            html += f"<tr><td><strong>{k['baslik']}</strong></td><td style='text-align:center; font-weight:bold;'>{k['max']}</td><td style='text-align:center; font-weight:900; font-size:1.1rem; color:{p_renk};'>{p}</td><td>{a}</td></tr>"
        genel = str(b.get('Genel Değerlendirme Yorumu', '-'))
        if pd.isna(genel) or not genel.strip() or genel.strip() == "nan": genel = "Genel değerlendirme yapılmadı."
        
        # HTML Tırnak Çakışması (SyntaxError) hatası tamamen düzeltildi
        html += f"</table><div class='yorum-kutu'><strong>💬 Genel Değerlendirme:</strong><br><br>{genel}</div><div class='imza'><strong>{ogrt_ad}</strong><br>{b.get('Ders', ogrt_brans)} Öğretmeni</div></div>"
    html += "</body></html>"
    return html


# ==========================================
# BÖLÜM 3: ÖĞRENCİ VE GİRİŞ PANELLERİ
# ==========================================
def ogrenci_paneli(df, ayarlar):
    st.markdown("<h2 style='text-align:center; color:#1e293b; font-weight:900; margin-bottom: 30px;'>🎓 Akıllı Karne Sorgulama Paneli</h2>", unsafe_allow_html=True)
    if df.empty: return st.warning("⚠️ Sisteme henüz veri yüklenmemiştir.")

    col_m = st.columns([1, 2, 1])[1]
    with col_m:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        secili_okul = st.selectbox("🏫 Okulunuz", ["— Okul Seçiniz —"] + ayarlar["okullar"])
        siniflar = ["— Sınıf Seçiniz —"] + sorted(df[df['Okul'] == secili_okul]['Sınıf'].dropna().unique().tolist()) if secili_okul != "— Okul Seçiniz —" else ["Önce okul seçin"]
        secili_sinif = st.selectbox("📚 Sınıfınız", siniflar)
        okul_no = st.text_input("🔢 Okul Numaranız")
        sorgula = st.button("🔍 Karnemi Bul", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if sorgula:
        if secili_okul == "— Okul Seçiniz —" or secili_sinif in ["— Sınıf Seçiniz —", "Önce okul seçin"] or not okul_no.strip(): st.error("❌ Eksik bilgi girdiniz.")
        else:
            ogrenci = df[(df['Okul'] == secili_okul) & (df['Sınıf'] == secili_sinif) & (df['Okul No'] == okul_no.strip())]
            if ogrenci.empty: st.error("❌ Kayıt bulunamadı.")
            else:
                bilgi = ogrenci.iloc[0] 
                ogrt_ad, ogrt_brans = ayarlar["kullanicilar"].get(bilgi.get('Ekleyen'), {}).get("ad", "Öğretmen"), ayarlar["kullanicilar"].get(bilgi.get('Ekleyen'), {}).get("brans", bilgi.get('Ders', "Genel"))
                st.success(f"🎉 Hoş geldin, {bilgi.get('Öğrenci Adı Soyadı', '')}!")
                html_karne = toplu_karne_html_dosyasi_uret(pd.DataFrame([bilgi]), ogrt_ad, ogrt_brans, CEKIRDEK_SABLON)
                st.components.v1.html(html_karne, height=700, scrolling=True)
                st.columns([1, 2, 1])[1].download_button("🖨️ İndir", data=html_karne, file_name=f"{bilgi['Ders']}_Karne_{bilgi['Okul No']}.html", mime="text/html", use_container_width=True)

def giris_paneli(ayarlar):
    col_m = st.columns([1, 1.2, 1])[1]
    with col_m:
        st.markdown('<div class="glass-card" style="padding:40px; text-align:center;"><h2 style="color:#2563eb; font-weight:900;">🔐 Sisteme Giriş</h2>', unsafe_allow_html=True)
        k_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("🚀 Giriş Yap", use_container_width=True):
            if ayarlar["kullanicilar"].get(k_adi) and ayarlar["kullanicilar"][k_adi]["sifre"] == sifre:
                st.session_state.update({"giris_yapti": True, "aktif_kullanici": k_adi, "kullanici_bilgi": ayarlar["kullanicilar"][k_adi]})
                st.rerun()
            else: st.error("❌ Hatalı giriş!")
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# BÖLÜM 4: YÖNETİM PANELİ (5 SEKME) VE ÇALIŞTIRMA
# ==========================================
def yonetim_paneli(df, ayarlar):
    aktif_id, k_bilgi, rol = st.session_state["aktif_kullanici"], st.session_state["kullanici_bilgi"], st.session_state["kullanici_bilgi"]["rol"]
    st.markdown(f'<div style="display:flex; justify-content:space-between; background:linear-gradient(135deg, #dbeafe, #bfdbfe); border-radius:12px; padding:15px; margin-bottom:20px;"><div><div style="font-weight:900; color:#1e40af; font-size:1.3rem;">👋 Hoş Geldiniz, {k_bilgi["ad"]}</div><div style="color:#2563eb; font-weight:700;">Yetki: {"Admin" if rol == "admin" else "Öğretmen"}</div></div></div>', unsafe_allow_html=True)
    if st.button("🚪 Çıkış Yap"): st.session_state.clear(); st.rerun()

    df_yetkili = df if rol == "admin" else df[(df['Okul'] == k_bilgi.get("okul")) & (df['Ekleyen'] == aktif_id)]
    sekmeler = st.tabs(["🏢 Şablon ve Sistem", "📂 Öğrenci Yükle/Ekle", "🤖 AI Değerlendirme", "📊 Raporlar", "📝 Akıllı Karne Görüşü"]) if rol == "admin" else st.tabs(["📂 Öğrenci Yükle/Ekle", "🤖 AI Değerlendirme", "📊 Raporlar", "📝 Akıllı Karne Görüşü"])

    # --- SEKME 1: SİSTEM (Sadece Admin) ---
    if rol == "admin":
        with sekmeler[0]:
            st.markdown("### 📚 Şablon Oluşturucu")
            if "taslak_df" not in st.session_state: st.session_state["taslak_df"] = pd.DataFrame([{"Kriter Başlığı": "İçerik", "Maksimum Puan": 50, "Açıklama": "Doğruluk"}])
            c_isim, c_kayit = st.columns([3, 1])
            s_isim = c_isim.text_input("Şablon Adı", value=st.session_state.get("edit_sablon_adi", ""))
            edited_df = st.data_editor(st.session_state["taslak_df"], num_rows="dynamic", use_container_width=True, hide_index=True)
            toplam_puan = pd.to_numeric(edited_df["Maksimum Puan"], errors="coerce").fillna(0).sum()
            if st.button("💾 Şablonu Kaydet", use_container_width=True):
                if toplam_puan != 100: st.error(f"Toplam 100 olmalı! ({toplam_puan})")
                elif s_isim.strip():
                    ayarlar["sablonlar"][s_isim] = [{"id": f"k{i+1}", "baslik": str(r["Kriter Başlığı"]), "max": int(r["Maksimum Puan"]), "icon": "📌", "aciklama": str(r["Açıklama"])} for i, r in edited_df.iterrows()]
                    ayar_kaydet(ayarlar); st.success("Kaydedildi!"); time.sleep(1); st.rerun()
            
            c_mevcut, c_ogrt = st.columns(2)
            with c_mevcut:
                secili_s = st.selectbox("Düzenle/Sil", ["— Seçiniz —"] + list(ayarlar.get("sablonlar", {}).keys()))
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("✏️ Düzenle") and secili_s != "— Seçiniz —":
                    st.session_state["taslak_df"] = pd.DataFrame([{"Kriter Başlığı": k["baslik"], "Maksimum Puan": k["max"], "Açıklama": k["aciklama"]} for k in ayarlar["sablonlar"][secili_s]])
                    st.session_state["edit_sablon_adi"] = secili_s; st.rerun() 
                if c_btn2.button("🗑️ Sil") and secili_s != "— Seçiniz —" and secili_s != "Gazi Matematik Şablonu":
                    del ayarlar["sablonlar"][secili_s]; ayar_kaydet(ayarlar); st.rerun()
            with c_ogrt:
                st.markdown("#### 👨‍🏫 Öğretmen Yönetimi")
                with st.form("o_ekle"):
                    o_kadi, o_sifre, o_ad = st.text_input("Kullanıcı Adı"), st.text_input("Şifre"), st.text_input("Ad Soyad")
                    if st.form_submit_button("Ekle") and o_kadi:
                        ayarlar["kullanicilar"][o_kadi] = {"sifre": o_sifre, "rol": "ogretmen", "ad": o_ad, "okul": ayarlar["okullar"][0], "brans": "Genel"}
                        ayar_kaydet(ayarlar); st.rerun()

    # --- SEKME 2: ÖĞRENCİ VERİ YÖNETİMİ ---
    with sekmeler[1] if rol == "admin" else sekmeler[0]:
        t1, t2, t3 = st.tabs(["📥 Excel Yükle", "➕ Manuel", "🗑️ Sil"])
        with t1:
            yuklenen = st.file_uploader("Excel Yükle", type=['xlsx'])
            if yuklenen and st.button("Yükle"):
                yeni_df = pd.read_excel(yuklenen, dtype={"Okul No": str}).dropna(subset=['Okul No'])
                yeni_df['Okul No'] = yeni_df['Okul No'].astype(str).str.strip().str.replace('.0', '', regex=False)
                yeni_df['Okul'], yeni_df['Ekleyen'], yeni_df['Dinamik_JSON'] = k_bilgi.get("okul", ayarlar["okullar"][0]), aktif_id, "{}"
                df = pd.concat([df, yeni_df[~yeni_df['Okul No'].isin(df['Okul No'].tolist())]], ignore_index=True)
                for s in GEREKLI_SUTUNLAR:
                    if s not in df.columns: df[s] = None
                veriyi_kaydet(df); st.success("Eklendi!"); time.sleep(1); st.rerun()
        with t3:
            s_okul = st.selectbox("Okul:", df_yetkili['Okul'].unique()) if not df_yetkili.empty else None
            if s_okul and st.button("🗑️ Okulu Komple Sil"):
                df = df[~(df['Okul'] == s_okul)] if rol == "admin" else df[~((df['Okul'] == s_okul) & (df['Ekleyen'] == aktif_id))]
                veriyi_kaydet(df); st.rerun()

    # --- SEKME 3: AI DEĞERLENDİRME ---
    with sekmeler[2] if rol == "admin" else sekmeler[1]:
        if not df_yetkili.empty:
            puan_liste = df_yetkili.apply(lambda r: f"{r['Okul No']} - {r['Öğrenci Adı Soyadı']}", axis=1).tolist()
            sec_p = st.selectbox("🎓 Öğrenci:", ["— Seçiniz —"] + puan_liste)
            secili_sablon = st.selectbox("📐 Şablon:", list(ayarlar.get("sablonlar", {}).keys()))
            aktif_sablon = ayarlar["sablonlar"].get(secili_sablon, CEKIRDEK_SABLON)
            
            if sec_p != "— Seçiniz —":
                idx = df[df['Okul No'] == sec_p.split(" - ")[0]].index[0]
                bilgi = df.iloc[idx]
                
                if st.session_state.get("aktif_ogr_idx") != idx:
                    st.session_state["aktif_ogr_idx"] = idx
                    eski = json.loads(bilgi.get('Dinamik_JSON', '{}')) if str(bilgi.get('Dinamik_JSON', '{}')).strip() not in ["nan", ""] else {}
                    for k in aktif_sablon:
                        st.session_state[f"w_puan_{k['id']}"] = int(pd.to_numeric(eski.get(f"{k['id']}_puan", bilgi.get(f"{k['baslik']} Puanı", 0)), errors='coerce')) if pd.notna(eski.get(f"{k['id']}_puan", bilgi.get(f"{k['baslik']} Puanı", 0))) else 0
                        st.session_state[f"w_aciklama_{k['id']}"] = str(eski.get(f"{k['id']}_aciklama", ""))
                    st.session_state["w_genel"] = str(bilgi.get('Genel Değerlendirme Yorumu', ""))

                ai_modu = st.radio("🤖 AI MODU:", ["A", "B", "C"], horizontal=True)
                ham_metin = st.text_input("Notunuz/Yorumunuz:") if ai_modu != "B" else ""
                hedef_puan = st.number_input("Hedef Puan", 0, 100, 85) if ai_modu == "B" else 0

                if st.button("✨ AI Çalıştır", use_container_width=True):
                    with st.spinner("Düşünüyor..."):
                        try:
                            m_puanlar = {k['id']: st.session_state.get(f"w_puan_{k['id']}", 0) for k in aktif_sablon}
                            sonuc = ai_degerlendirme_yap(bilgi.to_dict(), aktif_sablon, ai_modu, ham_metin, hedef_puan, m_puanlar, k_bilgi.get("ad", "Öğretmen"), bilgi.get("Ders", "Genel"))
                            for k in aktif_sablon:
                                if k['id'] in sonuc.get("puanlar", {}): st.session_state[f"w_puan_{k['id']}"] = int(sonuc["puanlar"][k['id']])
                                if k['id'] in sonuc.get("aciklamalar", {}): st.session_state[f"w_aciklama_{k['id']}"] = sonuc["aciklamalar"][k['id']]
                            if "genel" in sonuc: st.session_state["w_genel"] = sonuc["genel"]
                            st.rerun()
                        except Exception as e: st.error(e)

                for k in aktif_sablon:
                    c1, c2 = st.columns([1, 4])
                    c1.number_input(f"{k['baslik']} Max:{k['max']}", 0, k['max'], key=f"w_puan_{k['id']}")
                    c2.text_area(f"Açıklama", key=f"w_aciklama_{k['id']}")
                st.text_area("💬 Genel", key="w_genel")
                
                if st.button("💾 Kaydet"):
                    d_kayit, toplam = {}, 0
                    for k in aktif_sablon:
                        p, a = st.session_state[f"w_puan_{k['id']}"], st.session_state[f"w_aciklama_{k['id']}"]
                        d_kayit[f"{k['id']}_puan"], d_kayit[f"{k['id']}_aciklama"] = p, a
                        df.at[idx, f"{k['baslik']} Puanı"], df.at[idx, f"{k['baslik']} Açıklaması"] = p, str(a)
                        toplam += p
                    df.at[idx, 'Dinamik_JSON'], df.at[idx, 'Genel Değerlendirme Yorumu'], df.at[idx, 'Toplam Puan'] = json.dumps(d_kayit, ensure_ascii=False), str(st.session_state["w_genel"]), toplam
                    veriyi_kaydet(df); st.success(f"Kaydedildi! Puan: {toplam}")

    # --- SEKME 4: RAPORLAR ---
    with sekmeler[3] if rol == "admin" else sekmeler[2]:
        if not df_yetkili.empty:
            r_sinif = st.selectbox("Sınıf", sorted(df_yetkili['Sınıf'].dropna().unique()))
            df_yazdir = df_yetkili[df_yetkili['Sınıf'] == r_sinif]
            
            if st.radio("Tür:", ["Matris", "Normal"]) == "Matris":
                idare_df = pd.DataFrame({"Okul No": df_yazdir["Okul No"], "Öğrenci": df_yazdir["Öğrenci Adı Soyadı"]})
                for k in CEKIRDEK_SABLON: idare_df[f"{k['baslik']}"] = df_yazdir[f"{k['baslik']} Puanı"]
                idare_df["TOPLAM"] = df_yazdir["Toplam Puan"]
                st.dataframe(idare_df)
                
            if not df_yazdir.empty:
                html_cikti = toplu_karne_html_dosyasi_uret(df_yazdir, k_bilgi.get("ad", "Öğretmen"), df_yazdir.iloc[0].get("Ders", "Genel"), CEKIRDEK_SABLON)
                st.download_button("🖨️ HTML Karneleri İndir", html_cikti, file_name=f"{r_sinif}_Karneler.html", mime="text/html")

    # --- SEKME 5: AKILLI KARNE GÖRÜŞÜ ---
    with sekmeler[4] if rol == "admin" else sekmeler[3]:
        st.markdown("### 📝 Yapay Zeka Karne Görüşü")
        karne_dosya = st.file_uploader("Not Listesi (CSV/Excel)", type=['csv', 'xlsx', 'xls'])
        
        if karne_dosya:
            if "karne_df" not in st.session_state or st.session_state.get("son_yuklenen_karne") != karne_dosya.name:
                k_df = pd.read_csv(karne_dosya, sep=None, engine='python') if karne_dosya.name.endswith('.csv') else pd.read_excel(karne_dosya)
                if "AI_Karne_Gorusu" not in k_df.columns: k_df["AI_Karne_Gorusu"] = ""
                st.session_state["karne_df"], st.session_state["son_yuklenen_karne"] = k_df, karne_dosya.name
            
            if "karne_df" in st.session_state:
                k_df = st.session_state["karne_df"]
                kolonlar = k_df.columns.tolist()
                ad_k = next((c for c in kolonlar if "ad" in str(c).lower()), kolonlar[2] if len(kolonlar)>2 else kolonlar[0])
                sinif_k = next((c for c in kolonlar if "sınıf" in str(c).lower() or "sinif" in str(c).lower()), kolonlar[0])
                no_k = next((c for c in kolonlar if "no" in str(c).lower()), kolonlar[1] if len(kolonlar)>1 else kolonlar[0])
                ders_k = [c for c in kolonlar if c not in [ad_k, sinif_k, no_k, "AI_Karne_Gorusu"]]

                c_sol, c_sag = st.columns([1, 2])
                with c_sol:
                    ogr_liste = k_df.apply(lambda r: f"{r[no_k]} - {r[ad_k]}", axis=1).tolist()
                    secili_ogr = st.selectbox("Öğrenci Seç:", ["— Seçiniz —"] + ogr_liste)
                    davranis = st.text_area("Gözlem (Opsiyonel):")
                    
                    if secili_ogr != "— Seçiniz —":
                        secilen_no = secili_ogr.split(" - ")[0]
                        gercek_idx = k_df[k_df[no_k].astype(str) == str(secilen_no)].index[0]
                        bilgi = k_df.loc[gercek_idx]
                        
                        if st.button("✨ Görüş Yazdır", use_container_width=True):
                            with st.spinner("Yazılıyor..."):
                                try:
                                    gorus = ai_karne_gorusu_yaz(bilgi[ad_k], bilgi[sinif_k], {d: bilgi[d] for d in ders_k}, davranis, k_bilgi.get("ad", "Öğretmen"))
                                    st.session_state["karne_df"].at[gercek_idx, "AI_Karne_Gorusu"] = gorus
                                    st.success("Oluşturuldu!"); st.rerun()
                                except Exception as e: st.error(e)

                with c_sag:
                    if secili_ogr != "— Seçiniz —":
                        gercek_idx = k_df[k_df[no_k].astype(str) == str(secili_ogr.split(" - ")[0])].index[0]
                        yeni_gorus = st.text_area("Düzenle/Onayla:", value=st.session_state["karne_df"].at[gercek_idx, "AI_Karne_Gorusu"], height=150)
                        if st.button("💾 İşle"):
                            st.session_state["karne_df"].at[gercek_idx, "AI_Karne_Gorusu"] = yeni_gorus
                            st.success("Kaydedildi!")
                
                st.dataframe(st.session_state["karne_df"][[no_k, ad_k, "AI_Karne_Gorusu"]])
                
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as w: st.session_state["karne_df"].to_excel(w, index=False)
                st.download_button("📥 E-Okul Excel İndir", out.getvalue(), "Karneler.xlsx", "application/vnd.ms-excel")

def main():
    ayarlar, df = ayar_yukle(), veri_yukle()
    st.markdown('<div class="hero-header"><div class="hero-title">🏫 Proje ve Karne Yönetim Sistemi</div></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🎓 Öğrenci Girişi", "👨‍🏫 Yönetim Paneli"])
    with t1: ogrenci_paneli(df, ayarlar)
    with t2:
        if not st.session_state.get("giris_yapti", False): giris_paneli(ayarlar)
        else: yonetim_paneli(df, ayarlar)

if __name__ == "__main__":
    main()
