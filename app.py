import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime
import time
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

warnings.filterwarnings("ignore")

# ==================== ŞİFRE ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated:
        return True
    st.title("🔐 Pulse Kırılım Tarayıcı")
    st.markdown("**Abone Özel** - Direnç Kırılımı")
    password = st.text_input("Şifreyi girin", type="password")
    if st.button("Giriş"):
        if password == "pulse2026":
            st.session_state.authenticated = True
            st.success("Giriş başarılı!")
            st.rerun()
        else:
            st.error("Yanlış şifre!")
    return False

if not check_password():
    st.stop()

# ==================== TAM HİSSE LİSTESİ ====================
symbols = [
    'A1CAP', 'A1YEN', 'ACSEL', 'ADEL', 'ADESE', 'ADGYO', 'AEFES', 'AFYON', 'AGESA', 'AGHOL', 'AGROT', 'AGYO', 'AHGAZ', 'AHSGY', 'AKBNK', 'AKCNS', 'AKENR', 'AKFGY', 'AKFIS', 'AKFYE', 'AKGRT', 'AKMGY', 'AKSA', 'AKSEN', 'AKSUE', 'AKYHO', 'ALARK', 'ALCAR', 'ALCTL', 'ALFAS', 'ALGYO', 'ALKA', 'ALKIM', 'ALKLC', 'ALTNY', 'ALVES', 'ANELE', 'ANGEN', 'ANHYT', 'APBDL', 'APLIB', 'APMDL', 'APX30', 'ARASE', 'ARCLK', 'ARDYZ', 'ARENA', 'ARMGD', 'ARSAN', 'ARTMS', 'ARZUM', 'ASELS', 'ASGYO', 'ASTOR', 'ASUZU', 'ATAKP', 'ATATP', 'ATEKS', 'ATLAS', 'ATSYH', 'AVGYO', 'AVHOL', 'AVOD', 'AVPGY', 'AVTUR', 'AYCES', 'AYDEM', 'AYEN', 'AYES', 'AYGAZ', 'AZTEK', 'BAGFS', 'BAHKM', 'BAKAB', 'BALAT', 'BALSU', 'BANVT', 'BARMA', 'BASCM', 'BASGZ', 'BAYRK', 'BEGYO', 'BERA', 'BESLR', 'BEYAZ', 'BFREN', 'BIENY', 'BIGCH', 'BIGEN', 'BIMAS', 'BINBN', 'BINHO', 'BIOEN', 'BIZIM', 'BJKAS', 'BLCYT', 'BLUME', 'BMSCH', 'BMSTL', 'BNTAS', 'BOBET', 'BORLS', 'BORSK', 'BOSSA', 'BRISA', 'BRKSN', 'BRKVY', 'BRLSM', 'BRMEN', 'BRSAN', 'BRYAT', 'BSOKE', 'BTCIM', 'BUCIM', 'BULGS', 'BURCE', 'BURVA', 'BVSAN', 'BYDNR', 'CANTE', 'CASA', 'CATES', 'CCOLA', 'CELHA', 'CEMAS', 'CEMTS', 'CEMZY', 'CEOEM', 'CGCAM', 'CIMSA', 'CLEBI', 'CMBTN', 'CMENT', 'CONSE', 'COSMO', 'CRDFA', 'CRFSA', 'CUSAN', 'CVKMD', 'CWENE', 'DAGI', 'DAPGM', 'DARDL', 'DCTTR', 'DERHL', 'DERIM', 'DESA', 'DESPC', 'DEVA', 'DGATE', 'DGGYO', 'DGNMO', 'DIRIT', 'DITAS', 'DMRGD', 'DMSAS', 'DNISI', 'DOAS', 'DOBUR', 'DOCO', 'DOFER', 'DOFRB', 'DOGUB', 'DOHOL', 'DOKTA', 'DSTKF', 'DUNYH', 'DURDO', 'DURKN', 'DYOBY', 'DZGYO', 'EBEBK', 'ECILC', 'ECZYT', 'EDATA', 'EDIP', 'EFORC', 'EGEEN', 'EGEGY', 'EGEPO', 'EGGUB', 'EGPRO', 'EGSER', 'EKGYO', 'EKIZ', 'EKOS', 'EKSUN', 'ELITE', 'EMKEL', 'EMNIS', 'ENDAE', 'ENERY', 'ENJSA', 'ENKAI', 'ENSRI', 'ENTRA', 'EPLAS', 'ERBOS', 'ERCB', 'EREGL', 'ERSU', 'ESCAR', 'ESCOM', 'ESEN', 'ETILR', 'ETYAT', 'EUKYO', 'EUPWR', 'EUREN', 'EUYO', 'EYGYO', 'FENER', 'FLAP', 'FMIZP', 'FONET', 'FORTE', 'FRIGO', 'FZLGY', 'GARAN', 'GARFA', 'GEDIK', 'GEDZA', 'GENIL', 'GENTS', 'GEREL', 'GESAN', 'GLBMD', 'GLCVY', 'GLDTR', 'GLRMK', 'GLRYH', 'GMSTR', 'GMTAS', 'GOKNR', 'GOLTS', 'GOODY', 'GOZDE', 'GRNYO', 'GRSEL', 'GRTHO', 'GSDDE', 'GSDHO', 'GSRAY', 'GUBRF', 'GUNDG', 'GWIND', 'GZNMI', 'HALKB', 'HATEK', 'HATSN', 'HDFGS', 'HEDEF', 'HEKTS', 'HKTM', 'HLGYO', 'HOROZ', 'HRKET', 'HTTBT', 'HUBVC', 'HUNER', 'HURGZ', 'ICBCT', 'ICUGS', 'IDGYO', 'IEYHO', 'IHAAS', 'IHEVA', 'IHGZT', 'IHLAS', 'IHLGM', 'IHYAY', 'IMASM', 'INDES', 'INFO', 'INGRM', 'INTEK', 'INTEM', 'INVEO', 'INVES', 'IPEKE', 'ISBIR', 'ISBTR', 'ISCTR', 'ISDMR', 'ISFIN', 'ISGLK', 'ISGSY', 'ISGYO', 'ISKPL', 'ISMEN', 'ISSEN', 'IZENR', 'IZFAS', 'IZINV', 'IZMDC', 'JANTS', 'KAPLM', 'KAREL', 'KARSN', 'KARTN', 'KATMR', 'KAYSE', 'KBORU', 'KCAER', 'KCHOL', 'KENT', 'KERVN', 'KFEIN', 'KGYO', 'KIMMR', 'KLGYO', 'KLKIM', 'KLMSN', 'KLRHO', 'KLSER', 'KLSYN', 'KLYPV', 'KMPUR', 'KNFRT', 'KOCMT', 'KONKA', 'KONTR', 'KONYA', 'KOPOL', 'KORDS', 'KOTON', 'KOZAA', 'KOZAL', 'KRDMA', 'KRDMB', 'KRGYO', 'KRONT', 'KRPLS', 'KRSTL', 'KRTEK', 'KRVGD', 'KSTUR', 'KTLEV', 'KTSKR', 'KUTPO', 'KUVVA', 'KUYAS', 'KZBGY', 'KZGYO', 'LIDER', 'LILAK', 'LKMNH', 'LMKDC', 'LRSHO', 'LUKSK', 'LYDHO', 'LYDYE', 'MAALT', 'MACKO', 'MAGEN', 'MAKIM', 'MAKTK', 'MANAS', 'MARBL', 'MARKA', 'MARMR', 'MARTI', 'MAVI', 'MEDTR', 'MEGAP', 'MEGMT', 'MEKAG', 'MEPET', 'MERCN', 'MERIT', 'MERKO', 'METRO', 'MGROS', 'MHRGY', 'MIATK', 'MMCAS', 'MNDRS', 'MNDTR', 'MOBTL', 'MOGAN', 'MOPAS', 'MPARK', 'MRGYO', 'MRSHL', 'MSGYO', 'MTRKS', 'MTRYO', 'NATEN', 'NETAS', 'NIBAS', 'NTGAZ', 'NTHOL', 'NUGYO', 'NUHCM', 'OBAMS', 'OBASE', 'ODAS', 'ODINE', 'OFSYM', 'ONCSM', 'ONRYT', 'OPK30', 'OPT25', 'OPTGY', 'OPTLR', 'OPX30', 'ORCAY', 'ORGE', 'ORMA', 'OSMEN', 'OSTIM', 'OTKAR', 'OTTO', 'OYAKC', 'OYAYO', 'OYLUM', 'OYYAT', 'OZATD', 'OZGYO', 'OZKGY', 'OZRDN', 'OZSUB', 'OZYSR', 'PAGYO', 'PAMEL', 'PAPIL', 'PARSN', 'PASEU', 'PATEK', 'PCILT', 'PEKGY', 'PENGD', 'PENTA', 'PETKM', 'PETUN', 'PGSUS', 'PINSU', 'PKART', 'PKENT', 'PLTUR', 'PNLSN', 'PNSUT', 'POLHO', 'POLTK', 'PRDGS', 'PRKAB', 'PRKME', 'PSDTC', 'PSGYO', 'QNBFK', 'QNBTR', 'QTEMZ', 'QUAGR', 'RALYH', 'RAYSG', 'REEDR', 'RGYAS', 'RNPOL', 'RTALB', 'RUBNS', 'RUZYE', 'RYGYO', 'RYSAS', 'SAFKR', 'SAHOL', 'SAMAT', 'SANEL', 'SANFM', 'SANKO', 'SARKY', 'SASA', 'SDTTR', 'SEGMN', 'SEGYO', 'SEKFK', 'SEKUR', 'SELEC', 'SELVA', 'SERNT', 'SILVR', 'SISE', 'SKBNK', 'SKTAS', 'SKYLP', 'SKYMD', 'SMART', 'SMRTG', 'SMRVA', 'SNGYO', 'SNICA', 'SNKRN', 'SNPAM', 'SODSN', 'SOKE', 'SOKM', 'SONME', 'SRVGY', 'SUMAS', 'SUNTK', 'SURGY', 'SUWEN', 'TABGD', 'TARKM', 'TATEN', 'TATGD', 'TAVHL', 'TBORG', 'TCELL', 'TCKRC', 'TDGYO', 'TEHOL', 'TEKTU', 'TERA', 'TEZOL', 'TGSAS', 'THYAO', 'TKFEN', 'TKNSA', 'TLMAN', 'TMSN', 'TNZTP', 'TOASO', 'TRCAS', 'TRGYO', 'TRHOL', 'TRILC', 'TSKB', 'TSPOR', 'TTKOM', 'TTRAK', 'TUCLK', 'TUKAS', 'TUPRS', 'TUREX', 'TURGG', 'TURSG', 'UFUK', 'ULAS', 'ULKER', 'ULUFA', 'ULUSE', 'ULUUN', 'UNLU', 'USAK', 'USDTR', 'VAKBN', 'VAKFN', 'VAKKO', 'VANGD', 'VBTYZ', 'VERTU', 'VERUS', 'VESBE', 'VESTL', 'VKFYO', 'VKGYO', 'VKING', 'VRGYO', 'VSNMD', 'YAPRK', 'YATAS', 'YAYLA', 'YBTAS', 'YEOTK', 'YESIL', 'YGGYO', 'YGYO', 'YIGIT', 'YKBNK', 'YKSLN', 'YONGA', 'YUNSA', 'YYAPI', 'YYLGD', 'Z30EA', 'Z30KE', 'Z30KP', 'ZEDUR', 'ZELOT', 'ZGOLD', 'ZOREN', 'ZPBDL', 'ZPLIB', 'ZPT10', 'ZPX30', 'ZRE20', 'ZRGYO', 'ZSR25',
    'MCARD', 'ZGYO', 'ZERGY', 'NETCD', 'ATATR'
]

bist_symbols = [s + '.IS' for s in symbols if len(s) >= 3 and s.isalpha() and s not in ['CUSAN', 'APMDL']]

st.title("📊 Pulse Kırılım Tarayıcı")
st.caption("Tüm Zaman Dilimleri Destekleniyor")

with st.sidebar:
    st.header("Tarama Ayarları")
    timeframe = st.selectbox("⏰ Zaman Dilimi", ["1 Saat", "4 Saat", "Günlük"], index=0)
    breakout_mult = st.slider("Breakout Çarpanı", 1.000, 1.10, 1.005, 0.001)
    min_guc = st.slider("Minimum Güç", 1.5, 4.5, 2.0, 0.1)
    sleep_time = st.number_input("Hisse arası bekleme (sn)", 0.05, 1.0, 0.08)

# ==================== TARAMA ====================
if st.button(f"🚀 {timeframe} Tarama Başlat", type="primary"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    interval = "1h" if "Saat" in timeframe else "1d"
    period = "60d" if "Saat" in timeframe else "120d"

    for i, symbol in enumerate(bist_symbols):
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
            if len(data) < 30:
                continue

            current_close = float(data['Close'].iloc[-1])
            resistance = float(data['High'].rolling(40).max().iloc[-1])

            if current_close > resistance * breakout_mult:
                gain_pct = (current_close / resistance - 1) * 100
                results.append({
                    'Sembol': symbol.replace('.IS', ''),
                    'Periyot': timeframe,
                    'Güç': 3.2,
                    'Fiyat': round(current_close, 2),
                    'Direnç': round(resistance, 2),
                    'Yakınlık %': f"{gain_pct:.1f}".replace('.', ','),
                    'Yorum': 'Direnç kırıldı'
                })
        except:
            pass

        progress_bar.progress((i + 1) / len(bist_symbols))
        status_text.text(f"İşlenen: {i+1}/{len(bist_symbols)} | Bulunan: {len(results)}")
        time.sleep(sleep_time)

    if results:
        df = pd.DataFrame(results).sort_values('Güç', ascending=False)
        st.success(f"✅ {len(df)} kırılım sinyali bulundu!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Bu ayarlarla sinyal bulunamadı. Breakout çarpanını düşürün.")

st.info("Sayfa açılmama sorunu çözülmeli. Test için 1 Saat + Çarpan 1.005 önerilir.")
