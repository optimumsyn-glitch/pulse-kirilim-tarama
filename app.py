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

# Şifre (aynı)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.authenticated: return True
    st.title("🔐 Pulse Kırılım Tarayıcı")
    password = st.text_input("Şifreyi girin", type="password")
    if st.button("Giriş"):
        if password == "pulse2026":
            st.session_state.authenticated = True
            st.rerun()
    return False

if not check_password(): st.stop()

# Hisse listesi (kısaltılmış, senin listen aynı şekilde kalabilir)
symbols = ['MCARD', 'ZGYO', 'ZERGY', 'NETCD', 'ATATR', 'THYAO', 'GARAN', 'ASELS', 'BIMAS', 'TUPRS'] + [...]  # tam listenizi buraya koyun
bist_symbols = [s + '.IS' for s in symbols if len(s) >= 3 and s.isalpha()]

st.title("📊 Pulse Kırılım Tarayıcı")
with st.sidebar:
    timeframe = st.selectbox("Zaman Dilimi", ["1 Saat", "4 Saat", "Günlük"], index=0)
    BREAKOUT_MULTIPLIER = st.slider("Breakout Çarpanı", 1.000, 1.08, 1.003 if "Saat" in timeframe else 1.02, 0.001)
    MIN_STRENGTH = st.slider("Min Güç", 1.5, 4.5, 2.0 if "Saat" in timeframe else 2.5, 0.1)
    left_len = st.slider("Pivot Left", 3, 12, 6)
    right_len = st.slider("Pivot Right", 3, 12, 6)

tf_config = {"1 Saat": {"int":"1h","per":"60d"}, "4 Saat":{"int":"1h","per":"60d"}, "Günlük":{"int":"1d","per":"120d"}}
tf = tf_config[timeframe]

# ==================== FONKSİYONLAR ====================
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
    return df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()

def calculate_indicators_daily(df):
    if "4 Saat" in timeframe:  # tf["name"] yerine
        df = resample_to_4h(df)
    df = df.copy().reset_index(drop=True)
    if len(df) < 30: return df

    high = df['High'].values.flatten()
    low = df['Low'].values.flatten()
    close = df['Close'].values.flatten()
    volume = df['Volume'].values.flatten()

    df['pivot_high'] = ta_pivothigh(df['High'], left_len, right_len)
    df['last_resistance'] = df['pivot_high'].ffill()
    df['donchian_high'] = pd.Series(high).rolling(50 if "Saat" in timeframe else 20, min_periods=left_len).max()
    df['resistance_level'] = df['last_resistance'].fillna(df['donchian_high'])

    # ATR
    prev_close = np.roll(close, 1); prev_close[0] = close[0]
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])
    df['atr'] = pd.Series(tr).rolling(14, min_periods=1).mean()

    # RSI
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    gain_avg = pd.Series(gain).rolling(14, min_periods=1).mean()
    loss_avg = pd.Series(loss).rolling(14, min_periods=1).mean()
    df['rsi'] = 100 - (100 / (1 + gain_avg / (loss_avg + 1e-10)))
    df['rsi_in_zone'] = (df['rsi'] < 30) | (df['rsi'] > 70)

    df['volume_avg'] = pd.Series(volume).rolling(20, min_periods=1).mean()
    df['volume_increase'] = volume > df['volume_avg'] * 1.5

    # Momentum
    df['momentum_strong'] = pd.Series(close).diff(10) > 0

    # ADX & MACD (basitleştirildi)
    df['adx_strong'] = True
    df['macd_strong'] = True

    return df

def detect_very_strong_breakout(df, current_close, symbol):
    if len(df) < 30: return None
    last = df.iloc[-1]
    resistance = float(last.get('resistance_level', 0))
    if resistance <= 0 or pd.isna(resistance):
        return None

    if current_close < resistance * BREAKOUT_MULTIPLIER:
        return None

    strength = 1.5 if last.get('rsi_in_zone', False) else 0
    strength += 1.5 if last.get('volume_increase', False) else 0
    strength += 1.0 if last.get('momentum_strong', False) else 0
    strength = min(strength, 5.0)

    if strength < MIN_STRENGTH:
        return None

    gain_pct = (current_close / resistance - 1) * 100
    uzaklik = f"{gain_pct:.1f}".replace('.', ',')
    kategori = "Çok Yakın" if gain_pct <= 5 else "Yakın" if gain_pct <= 12 else "Orta"

    return {
        'Sembol': symbol.replace('.IS', ''),
        'Periyot': timeframe,
        'Güç': round(strength, 1),
        'Fiyat': round(current_close, 2),
        'Direnç': round(resistance, 2),
        'Yakınlık %': uzaklik,
        'Yakınlık': kategori,
        'Yorum': "Saatlik güçlü kırılım tespit edildi."
    }

# ==================== TARAMA ====================
if st.button(f"🚀 {timeframe} Tarama Başlat", type="primary"):
    results = []
    with st.spinner("Tarama devam ediyor..."):
        bar = st.progress(0)
        for i, sym in enumerate(bist_symbols):
            try:
                data = yf.download(sym, period=tf["per"], interval=tf["int"], progress=False)
                if len(data) < 30: continue
                close = float(data['Close'].iloc[-1])
                dfi = calculate_indicators_daily(data)
                res = detect_very_strong_breakout(dfi, close, sym)
                if res:
                    results.append(res)
            except:
                pass
            bar.progress((i+1)/len(bist_symbols))
            time.sleep(0.08)

    if results:
        df = pd.DataFrame(results).sort_values('Güç', ascending=False)
        st.success(f"✅ {len(df)} sinyal bulundu!")
        st.dataframe(df)
    else:
        st.error("Hala sinyal bulunamadı. Breakout Çarpanı'nı 1.003'e düşürün.")

st.info("Saatlik taramada Breakout Çarpanı'nı düşük tutun (1.003 - 1.008)")
