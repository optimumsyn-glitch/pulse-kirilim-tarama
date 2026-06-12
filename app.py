import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
import time
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment

warnings.filterwarnings("ignore")

# ==================== ŞİFRE ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated:
        return True
    st.title("🔐 Pulse Kırılım Tarayıcı")
    st.markdown("**Abone Özel**")
    pw = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        if pw == "pulse2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Yanlış şifre")
    return False

if not check_password():
    st.stop()

# ==================== AYARLAR ====================
st.title("📊 Pulse Kırılım Tarayıcı")

with st.sidebar:
    st.header("Ayarlar")
    periyot = st.selectbox("Zaman Dilimi", ["1 Saat", "4 Saat", "Günlük"], index=0)
    carp an = st.slider("Breakout Çarpanı", 1.000, 1.08, 1.005, 0.001)
    min_guc = st.slider("Minimum Güç", 1.5, 4.5, 2.0, 0.1)
    test_mode = st.checkbox("Sadece Test Hisseleri (Hızlı)", value=True)

# ==================== HİSSE LİSTESİ ====================
if test_mode:
    symbols = ['MCARD', 'ZGYO', 'ZERGY', 'NETCD', 'ATATR', 'THYAO', 'GARAN', 'ASELS', 'BIMAS', 'TUPRS', 'SASA', 'EREGL']
else:
    symbols = ['A1CAP', 'A1YEN', ...]  # buraya tam listeni koyabilirsin

bist_symbols = [s + '.IS' for s in symbols]

tf_map = {
    "1 Saat": {"int": "1h", "per": "60d"},
    "4 Saat": {"int": "1h", "per": "60d"},
    "Günlük": {"int": "1d", "per": "120d"}
}
tf = tf_map[periyot]

# ==================== FONKSİYONLAR ====================
def calculate_indicators(df):
    df = df.copy().reset_index(drop=True)
    if len(df) < 30:
        return df
    
    high = df['High'].values
    close = df['Close'].values
    volume = df['Volume'].values

    # Basit pivot + resistance
    df['resistance_level'] = df['High'].rolling(50).max()

    # Basit indikatörler
    df['volume_increase'] = volume > pd.Series(volume).rolling(20).mean() * 1.5
    df['rsi_in_zone'] = True  # basitleştirildi
    df['momentum_strong'] = pd.Series(close).diff(8) > 0

    return df

def detect_breakout(df, current_close, symbol):
    if len(df) < 30:
        return None
    last = df.iloc[-1]
    resistance = float(last['resistance_level'])
    if resistance <= 0 or pd.isna(resistance):
        return None

    if current_close < resistance * carpan:
        return None

    strength = 2.5
    if last['volume_increase']:
        strength += 1.0
    if last['momentum_strong']:
        strength += 0.8

    if strength < min_guc:
        return None

    gain = (current_close / resistance - 1) * 100

    return {
        'Sembol': symbol.replace('.IS', ''),
        'Periyot': periyot,
        'Güç': round(strength, 1),
        'Fiyat': round(current_close, 2),
        'Direnç': round(resistance, 2),
        'Yakınlık %': f"{gain:.1f}".replace('.', ','),
        'Yorum': 'Kırılım tespit edildi'
    }

# ==================== TARAMA ====================
if st.button(f"🚀 {periyot} Tarama Başlat", type="primary"):
    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, symbol in enumerate(bist_symbols):
        try:
            data = yf.download(symbol, period=tf["per"], interval=tf["int"], 
                             progress=False, auto_adjust=True, timeout=10)
            if len(data) < 30:
                continue

            current = float(data['Close'].iloc[-1])
            df_ind = calculate_indicators(data)
            result = detect_breakout(df_ind, current, symbol)

            if result:
                results.append(result)
                st.success(f"✅ {result['Sembol']} | Güç: {result['Güç']}")

        except:
            pass

        progress.progress((i+1)/len(bist_symbols))
        status.text(f"İşlenen: {i+1}/{len(bist_symbols)} | Bulunan: {len(results)}")
        time.sleep(0.1)

    if results:
        df = pd.DataFrame(results).sort_values('Güç', ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sinyal bulunamadı. Breakout çarpanını düşürün.")

st.caption("Sorun devam ederse 'Test Modu' açık olsun.")
