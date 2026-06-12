import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
import time
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Pulse Kırılım Tarayıcı", layout="wide")

# ==================== ŞİFRE VE OTURUM YÖNETİMİ ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated:
        return True
    
    st.title("🔐 Pulse Kırılım Tarayıcı")
    st.markdown("**Abone Özel** — Direnç Kırılımı Sinyalleri")
    
    with st.form("login_form"):
        password = st.text_input("Şifreyi girin", type="password")
        submit = st.form_submit_button("Giriş Yap")
        
        if submit:
            if password == "pulse2026":
                st.session_state.authenticated = True
                st.success("Giriş başarılı! Lütfen sayfayı bir kez yenileyin veya butona tekrar basın.")
                st.rerun()
            else:
                st.error("Yanlış şifre!")
    return False

if not check_password():
    st.stop()

# ==================== HİSSE LİSTESİ VE DİNAMİK KONTROL ====================
symbols = [
    'A1CAP', 'A1YEN', 'ACSEL', 'ADEL', 'ADESE', 'ADGYO', 'AEFES', 'AFYON', 'AGESA', 'AGHOL', 'AGROT', 'AGYO', 'AHGAZ', 'AHSGY', 'AKBNK', 'AKCNS', 'AKENR', 'AKFGY', 'AKFIS', 'AKFYE', 'AKGRT', 'AKMGY', 'AKSA', 'AKSEN', 'AKSUE', 'AKYHO', 'ALARK', 'ALCAR', 'ALCTL', 'ALFAS', 'ALGYO', 'ALKA', 'ALKIM', 'ALKLC', 'ALTNY', 'ALVES', 'ANELE', 'ANGEN', 'ANHYT', 'APBDL', 'APLIB', 'APMDL', 'APX30', 'ARASE', 'ARCLK', 'ARDYZ', 'ARENA', 'ARMGD', 'ARSAN', 'ARTMS', 'ARZUM', 'ASELS', 'ASGYO', 'ASTOR', 'ASUZU', 'ATAKP', 'ATATP', 'ATEKS', 'ATLAS', 'ATSYH', 'AVGYO', 'AVHOL', 'AVOD', 'AVPGY', 'AVTUR', 'AYCES', 'AYDEM', 'AYEN', 'AYES', 'AYGAZ', 'AZTEK', 'BAGFS', 'BAHKM', 'BAKAB', 'BALAT', 'BALSU', 'BANVT', 'BARMA', 'BASCM', 'BASGZ', 'BAYRK', 'BEGYO', 'BERA', 'BESLR', 'BEYAZ', 'BFREN', 'BIENY', 'BIGCH', 'BIGEN', 'BIMAS', 'BINBN', 'BINHO', 'BIOEN', 'BIZIM', 'BJKAS', 'BLCYT', 'BLUME', 'BMSCH', 'BMSTL', 'BNTAS', 'BOBET', 'BORLS', 'BORSK', 'BOSSA', 'BRISA', 'BRKSN', 'BRKVY', 'BRLSM', 'BRMEN', 'BRSAN', 'BRYAT', 'BSOKE', 'BTCIM', 'BUCIM', 'BULGS', 'BURCE', 'BURVA', 'BVSAN', 'BYDNR', 'CANTE', 'CASA', 'CATES', 'CCOLA', 'CELHA', 'CEMAS', 'CEMTS', 'CEMZY', 'CEOEM', 'CGCAM', 'CIMSA', 'CLEBI', 'CMBTN', 'CMENT', 'CONSE', 'COSMO', 'CRDFA', 'CRFSA', 'CUSAN', 'CVKMD', 'CWENE', 'DAGI', 'DAPGM', 'DARDL', 'DCTTR', 'DERHL', 'DERIM', 'DESA', 'DESPC', 'DEVA', 'DGATE', 'DGGYO', 'DGNMO', 'DIRIT', 'DITAS', 'DMRGD', 'DMSAS', 'DNISI', 'DOAS', 'DOBUR', 'DOCO', 'DOFER', 'DOFRB', 'DOGUB', 'DOHOL', 'DOKTA', 'DSTKF', 'DUNYH', 'DURDO', 'DURKN', 'DYOBY', 'DZGYO', 'EBEBK', 'ECILC', 'ECZYT', 'EDATA', 'EDIP', 'EFORC', 'EGEEN', 'EGEGY', 'EGEPO', 'EGGUB', 'EGPRO', 'EGSER', 'EKGYO', 'EKIZ', 'EKOS', 'EKSUN', 'ELITE', 'EMKEL', 'EMNIS', 'ENDAE', 'ENERY', 'ENJSA', 'ENKAI', 'ENSRI', 'ENTRA', 'EPLAS', 'ERBOS', 'ERCB', 'EREGL', 'ERSU', 'ESCAR', 'ESCOM', 'ESEN', 'ETILR', 'ETYAT', 'EUKYO', 'EUPWR', 'EUREN', 'EUYO', 'EYGYO', 'FENER', 'FLAP', 'FMIZP', 'FONET', 'FORTE', 'FRIGO', 'FZLGY', 'GARAN', 'GARFA', 'GEDIK', 'GEDZA', 'GENIL', 'GENTS', 'GEREL', 'GESAN', 'GLBMD', 'GLCVY', 'GLDTR', 'GLRMK', 'GLRYH', 'GMSTR', 'GMTAS', 'GOKNR', 'GOLTS', 'GOODY', 'GOZDE', 'GRNYO', 'GRSEL', 'GRTHO', 'GSDDE', 'GSDHO', 'GSRAY', 'GUBRF', 'GUNDG', 'GWIND', 'GZNMI', 'HALKB', 'HATEK', 'HATSN', 'HDFGS', 'HEDEF', 'HEKTS', 'HKTM', 'HLGYO', 'HOROZ', 'HRKET', 'HTTBT', 'HUBVC', 'HUNER', 'HURGZ', 'ICBCT', 'ICUGS', 'IDGYO', 'IEYHO', 'IHAAS', 'IHEVA', 'IHGZT', 'IHLAS', 'IHLGM', 'IHYAY', 'IMASM', 'INDES', 'INFO', 'INGRM', 'INTEK', 'INTEM', 'INVEO', 'INVES', 'IPEKE', 'ISBIR', 'ISBTR', 'ISCTR', 'ISDMR', 'ISFIN', 'ISGLK', 'ISGSY', 'ISGYO', 'ISKPL', 'ISMEN', 'ISSEN', 'IZENR', 'IZFAS', 'IZINV', 'IZMDC', 'JANTS', 'KAPLM', 'KAREL', 'KARSN', 'KARTN', 'KATMR', 'KAYSE', 'KBORU', 'KCAER', 'KCHOL', 'KENT', 'KERVN', 'KFEIN', 'KGYO', 'KIMMR', 'KLGYO', 'KLKIM', 'KLMSN', 'KLRHO', 'KLSER', 'KLSYN', 'KLYPV', 'KMPUR', 'KNFRT', 'KOCMT', 'KONKA', 'KONTR', 'KONYA', 'KOPOL', 'KORDS', 'KOTON', 'KOZAA', 'KOZAL', 'KRDMA', 'KRDMB', 'KRGYO', 'KRONT', 'KRPLS', 'KRSTL', 'KRTEK', 'KRVGD', 'KSTUR', 'KTLEV', 'KTSKR', 'KUTPO', 'KUVVA', 'KUYAS', 'KZBGY', 'KZGYO', 'LIDER', 'LILAK', 'LKMNH', 'LMKDC', 'LRSHO', 'LUKSK', 'LYDHO', 'LYDYE', 'MAALT', 'MACKO', 'MAGEN', 'MAKIM', 'MAKTK', 'MANAS', 'MARBL', 'MARKA', 'MARMR', 'MARTI', 'MAVI', 'MEDTR', 'MEGAP', 'MEGMT', 'MEKAG', 'MEPET', 'MERCN', 'MERIT', 'MERKO', 'METRO', 'MGROS', 'MHRGY', 'MIATK', 'MMCAS', 'MNDRS', 'MNDTR', 'MOBTL', 'MOGAN', 'MOPAS', 'MPARK', 'MRGYO', 'MRSHL', 'MSGYO', 'MTRKS', 'MTRYO', 'NATEN', 'NETAS', 'NIBAS', 'NTGAZ', 'NTHOL', 'NUGYO', 'NUHCM', 'OBAMS', 'OBASE', 'ODAS', 'ODINE', 'OFSYM', 'ONCSM', 'ONRYT', 'OPK30', 'OPT25', 'OPTGY', 'OPTLR', 'OPX30', 'ORCAY', 'ORGE', 'ORMA', 'OSMEN', 'OSTIM', 'OTKAR', 'OTTO', 'OYAKC', 'OYAYO', 'OYLUM', 'OYYAT', 'OZATD', 'OZGYO', 'OZKGY', 'OZRDN', 'OZSUB', 'OZYSR', 'PAGYO', 'PAMEL', 'PAPIL', 'PARSN', 'PASEU', 'PATEK', 'PCILT', 'PEKGY', 'PENGD', 'PENTA', 'PETKM', 'PETUN', 'PGSUS', 'PINSU', 'PKART', 'PKENT', 'PLTUR', 'PNLSN', 'PNSUT', 'POLHO', 'POLTK', 'PRDGS', 'PRKAB', 'PRKME', 'PSDTC', 'PSGYO', 'QNBFK', 'QNBTR', 'QTEMZ', 'QUAGR', 'RALYH', 'RAYSG', 'REEDR', 'RGYAS', 'RNPOL', 'RTALB', 'RUBNS', 'RUZYE', 'RYGYO', 'RYSAS', 'SAFKR', 'SAHOL', 'SAMAT', 'SANEL', 'SANFM', 'SANKO', 'SARKY', 'SASA', 'SDTTR', 'SEGMN', 'SEGYO', 'SEKFK', 'SEKUR', 'SELEC', 'SELVA', 'SERNT', 'SILVR', 'SISE', 'SKBNK', 'SKTAS', 'SKYLP', 'SKYMD', 'SMART', 'SMRTG', 'SMRVA', 'SNGYO', 'SNICA', 'SNKRN', 'SNPAM', 'SODSN', 'SOKE', 'SOKM', 'SONME', 'SRVGY', 'SUMAS', 'SUNTK', 'SURGY', 'SUWEN', 'TABGD', 'TARKM', 'TATEN', 'TATGD', 'TAVHL', 'TBORG', 'TCELL', 'TCKRC', 'TDGYO', 'TEHOL', 'TEKTU', 'TERA', 'TEZOL', 'TGSAS', 'THYAO', 'TKFEN', 'TKNSA', 'TLMAN', 'TMSN', 'TNZTP', 'TOASO', 'TRCAS', 'TRGYO', 'TRHOL', 'TRILC', 'TSKB', 'TSPOR', 'TTKOM', 'TTRAK', 'TUCLK', 'TUKAS', 'TUPRS', 'TUREX', 'TURGG', 'TURSG', 'UFUK', 'ULAS', 'ULKER', 'ULUFA', 'ULUSE', 'ULUUN', 'UNLU', 'USAK', 'USDTR', 'VAKBN', 'VAKFN', 'VAKKO', 'VANGD', 'VBTYZ', 'VERTU', 'VERUS', 'VESBE', 'VESTL', 'VKFYO', 'VKGYO', 'VKING', 'VRGYO', 'VSNMD', 'YAPRK', 'YATAS', 'YAYLA', 'YBTAS', 'YEOTK', 'YESIL', 'YGGYO', 'YGYO', 'YIGIT', 'YKBNK', 'YKSLN', 'YONGA', 'YUNSA', 'YYAPI', 'YYLGD', 'Z30EA', 'Z30KE', 'Z30KP', 'ZEDUR', 'ZELOT', 'ZGOLD', 'ZOREN', 'ZPBDL', 'ZPLIB', 'ZPT10', 'ZPX30', 'ZRE20', 'ZRGYO', 'ZSR25'
]

# Eksik listelenen kağıtlar yoksa ekleniyor
eklenecekler = ['MCARD', 'NETCD', 'ATATR', 'ZERGY', 'ZGYO']
for h in eklenecekler:
    if h not in symbols:
        symbols.append(h)

valid_symbols = [s for s in symbols if len(s) >= 3 and s.isalpha() and s not in ['CUSAN', 'APMDL']]
bist_symbols = [s + '.IS' for s in valid_symbols]

# ==================== SIDEBAR / ARAYÜZ AYARLARI ====================
st.sidebar.header("Tarama Ayarları")

timeframe = st.sidebar.selectbox("⏰ Zaman Dilimi", 
    ["1s", "4s", "Günlük", "Haftalık", "Aylık"], index=2)

left_len = st.sidebar.slider("Pivot Left Len", 3, 10, 5)
right_len = st.sidebar.slider("Pivot Right Len", 3, 10, 5)
donchian_period = st.sidebar.slider("Donchian Period", 10, 60, 20)

BREAKOUT_MULTIPLIER = st.sidebar.slider("Breakout Çarpanı", 1.000, 1.10, 1.02, 0.001)
MIN_STRENGTH = st.sidebar.slider("Minimum Güç", 1.8, 4.5, 2.5, 0.1)

sleep_time = st.sidebar.number_input("Hisse arası bekleme (sn)", 0.00, 2.0, 0.05)

tf_config = {
    "1s": {"interval": "1h", "period": "30d", "name": "1s"},
    "4s": {"interval": "1h", "period": "60d", "name": "4s"}, # 1h çekilip 4h'e resample edilir
    "Günlük": {"interval": "1d", "period": "150d", "name": "daily"},
    "Haftalık": {"interval": "1wk", "period": "3y", "name": "weekly"},
    "Aylık": {"interval": "1mo", "period": "5y", "name": "monthly"}
}
tf = tf_config[timeframe]

st.title("📊 Pulse Kırılım Tarayıcı")
st.write(f"Şu anki Seçim: **{timeframe}** Periyodu | Toplam Aktif Hisse Senedi Sayısı: **{len(bist_symbols)}**")

# ==================== TEKNİK HESAPLAMALAR ====================
def ta_pivothigh(series, left, right):
    series = series.values.flatten()
    result = np.full(len(series), np.nan)
    for i in range(left, len(series) - right):
        if series[i] >= max(series[i-left:i]) and series[i] >= max(series[i+1:i+right+1]):
            result[i] = series[i]
    return pd.Series(result)

def resample_to_4h(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    ohlc = {'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}
    return df.resample('4H').agg(ohlc).dropna()

def calculate_indicators_daily(df):
    if tf["name"] == "4s":
        df = resample_to_4h(df)
        
    df = df.copy().reset_index(drop=True)
    high = df['High'].values.flatten()
    low = df['Low'].values.flatten()
    close = df['Close'].values.flatten()
    volume = df['Volume'].values.flatten()

    df['pivot_high'] = ta_pivothigh(df['High'], left_len, right_len)
    df['last_resistance'] = df['pivot_high'].ffill()
    df['donchian_high'] = pd.Series(high).rolling(donchian_period, min_periods=left_len).max()
    df['resistance_level'] = df['last_resistance'].fillna(df['donchian_high'])

    prev_close = np.roll(close, 1); prev_close[0] = close[0]
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])
    df['atr'] = pd.Series(tr).rolling(14, min_periods=1).mean()

    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    gain_avg = pd.Series(gain).rolling(14, min_periods=1).mean()
    loss_avg = pd.Series(loss).rolling(14, min_periods=1).mean()
    rs = gain_avg / (loss_avg + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi_in_zone'] = (df['rsi'] < 30) | (df['rsi'] > 70)

    df['volume_avg'] = pd.Series(volume).rolling(20, min_periods=1).mean()
    df['volume_increase'] = volume > df['volume_avg'] * 1.5

    momentum = pd.Series(close).diff(10)
    momentum_sma = momentum.rolling(10, min_periods=1).mean()
    df['momentum_strong'] = (momentum > 0) & (momentum > momentum_sma)

    plus_dm = np.diff(high, prepend=high[0]); plus_dm[plus_dm < 0] = 0
    minus_dm = np.diff(low, prepend=low[0]); minus_dm = -minus_dm; minus_dm[minus_dm < 0] = 0
    tr_smooth = pd.Series(tr).rolling(14, min_periods=1).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(14, min_periods=1).mean() / (tr_smooth + 1e-10)
    minus_di = 100 * pd.Series(minus_dm).rolling(14, min_periods=1).mean() / (tr_smooth + 1e-10)
    dx = np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10) * 100
    df['adx'] = dx.rolling(14, min_periods=1).mean()
    df['adx_strong'] = df['adx'] > 25

    ema12 = pd.Series(close).ewm(span=12, adjust=False).mean()
    ema26 = pd.Series(close).ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    df['macd_strong'] = (macd_line > signal_line) & (macd_line > 0)

    return df

def get_yakinlik_kategori(gain_pct):
    if gain_pct <= 3:
        return f"{gain_pct:.1f}".replace('.', ','), "Çok Yakın"
    elif gain_pct <= 7:
        return f"{gain_pct:.1f}".replace('.', ','), "Yakın"
    elif gain_pct <= 15:
        return f"{gain_pct:.1f}".replace('.', ','), "Orta"
    else:
        return f"{gain_pct:.1f}".replace('.', ','), "Uzak"

def generate_yorum(guc, yakinlik_kategori, yakinlik_pct_str):
    pct = float(yakinlik_pct_str.replace(',', '.'))
    if guc >= 4.0:
        if pct <= 3.0:
            return "Direnci kırdı, artık direnç destek oldu. Kısa vadede kar realizasyonu gelebilir, stop seviyesi biraz altı takip edilmeli."
        elif pct <= 7.0:
            return "Güçlü kırılım gerçekleşti. Destek olarak çalışabilir. Kar satışları kısa vadede gelebilir, dikkatli olun."
        else:
            return "Çok güçlü kırılım ama fiyat bayağı uzaklaştı. Kar realizasyonunu unutmayın, kısa vadeli düzeltme gelebilir."
    elif guc >= 3.0:
        if pct <= 7.0:
            return "Kırılım onaylandı, direnç → destek dönüşümü olası. Kar realizasyonu riski orta seviyede. Stop seviyesi direncin biraz altına konulabilir."
        else:
            return "Kırılım gerçekleşti ancak mesafe açıldı. Kar satışları gelebilir, kısa vadeli dikkat gerekli."
    else:
        return "Kırılım eşiğinde güçlü sinyal. Direnç destek olabilir ama onay bekleniyor. Kar realizasyonu kısa vadede gelebilir."

def detect_very_strong_breakout(df_daily, current_close, symbol):
    if len(df_daily) < 20:
        return None
    last_row = df_daily.iloc[-1]
    resistance = float(last_row['resistance_level'])
    if pd.isna(resistance) or resistance <= 0:
        return None

    if current_close < resistance * BREAKOUT_MULTIPLIER:
        return None

    # yfinance veri yapısındaki kaymaları önlemek için serilerden skaler değere dönüşüm sağlandı
    rsi_ok = bool(last_row['rsi_in_zone'])
    volume_ok = bool(last_row['volume_increase'])
    atr_ok = float(last_row['atr']) > float(df_daily['atr'].iloc[-2]) if len(df_daily) > 1 else True
    momentum_ok = bool(last_row['momentum_strong'])
    adx_ok = bool(last_row['adx_strong'])
    macd_ok = bool(last_row['macd_strong'])

    strength = 0.0
    if rsi_ok: strength += 1.5
    if volume_ok: strength += 1.5
    if atr_ok: strength += 1.0
    if momentum_ok: strength += 0.7
    if adx_ok: strength += 0.7
    if macd_ok: strength += 0.7

    count = sum([rsi_ok, volume_ok, atr_ok, momentum_ok, adx_ok, macd_ok])
    if count >= 3: strength = max(strength, 2.5)
    strength = min(strength, 5.0)

    if strength < MIN_STRENGTH:
        return None

    gain_pct = (current_close / resistance - 1) * 100
    uzaklik, kategori = get_yakinlik_kategori(gain_pct)
    yorum = generate_yorum(strength, kategori, uzaklik)

    return {
        'Sembol': symbol.replace('.IS', ''),
        'Periyot': timeframe,
        'Tür': 'Kırılım AL',
        'Kategori': 'Çok Güçlü' if strength >= 4.0 else 'Güçlü',
        'Güç': round(strength, 1),
        'Fiyat': round(current_close, 2),
        'Direnç': round(resistance, 2),
        'Yakınlık %': uzaklik,
        'Yakınlık': kategori,
        'Yorum': yorum
    }

# ==================== MOTOR ÇALIŞTIRMA VE GÖRÜNTÜLEME ====================
if st.button(f"🚀 {timeframe} Tarama Başlat", type="primary"):
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_found_text = st.empty()

    for i, symbol in enumerate(bist_symbols):
        try:
            data = yf.download(symbol, period=tf["period"], interval=tf["interval"], 
                               progress=False, auto_adjust=True)
            if data.empty or len(data) < 20:
                continue

            # Son güncel kapanış değerini tekil float olarak yakalama
            current_close = float(data['Close'].iloc[-1].item() if hasattr(data['Close'].iloc[-1], 'item') else data['Close'].iloc[-1])
            
            df_ind = calculate_indicators_daily(data)
            result = detect_very_strong_breakout(df_ind, current_close, symbol)

            if result:
                results.append(result)
                live_found_text.success(f"🔥 YENİ BULUNDU → **{result['Sembol']}** | Güç: {result['Güç']} | Kategori: {result['Yakınlık']}")

            progress_bar.progress((i + 1) / len(bist_symbols))
            status_text.info(f"İşlenen Hisse: {i+1}/{len(bist_symbols)} | Toplam Sinyal: {len(results)}")

        except Exception as e:
            continue
        if sleep_time > 0:
            time.sleep(sleep_time)

    status_text.empty()
    live_found_text.empty()

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by=['Güç', 'Fiyat'], ascending=[False, True]).reset_index(drop=True)
        
        st.success(f"✅ Tarama bitti! Toplam {len(df)} adet güçlü kırılım sinyali listeleniyor.")
        st.dataframe(df, use_container_width=True)

        # Profesyonel Excel Oluşturma Alanı
        output = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Kırılım Sinyalleri"
        
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        # Stil ve Format Renklendirmesi
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="1F497D")
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                             top=Side(style='thin'), bottom=Side(style='thin'))

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='left', vertical='center')

        wb.save(output)
        output.seek(0)

        st.download_button(
            label="📥 Excel Sonuç Raporunu İndir",
            data=output,
            file_name=f"Pulse_Tarama_{tf['name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning(f"Seçilen '{timeframe}' zaman diliminde strateji kriterlerine uyan herhangi bir hisse senedi kırılımı saptanmadı.")

st.info("Not: Tarama esnasında tarayıcı sekmesini kapatmayın ya da sayfayı yenilemeyin.")
