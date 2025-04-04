import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# -------------------- USTAWIENIA --------------------
st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📊 Trading Dashboard 5m - LONG & SHORT + Skuteczność")
ticker = st.sidebar.selectbox("Wybierz instrument:", ["BTC-USD", "ETH-USD", "AAPL", "SPY"])

# -------------------- POBIERANIE DANYCH --------------------
df = yf.download(ticker, period="7d", interval="5m")

# -------------------- RSI --------------------
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# -------------------- MACD --------------------
def calculate_macd(data):
    exp1 = data.ewm(span=12, adjust=False).mean()
    exp2 = data.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

# -------------------- OBLICZENIA --------------------
df["RSI"] = calculate_rsi(df["Close"])
df["MACD"], df["MACD_signal"], df["MACD_hist"] = calculate_macd(df["Close"])

# -------------------- STRATEGIA --------------------
trades = []
position = None
entry_price = 0

for i in range(2, len(df)):
    rsi = df["RSI"].iloc[i]
    macdh = df["MACD_hist"].iloc[i]
    prev_macdh = df["MACD_hist"].iloc[i - 1]
    price = df["Close"].iloc[i]

    if position is None:
        if rsi < 30 and prev_macdh < 0 and macdh > 0:
            position = "LONG"
            entry_price = price
        elif rsi > 70 and prev_macdh > 0 and macdh < 0:
            position = "SHORT"
            entry_price = price
    else:
        if position == "LONG" and (rsi > 60 or macdh < 0):
            pnl = float(price) - float(entry_price)
            if isinstance(pnl, (int, float)):
                trades.append(pnl)
            position = None
        elif position == "SHORT" and (rsi < 50 or macdh > 0):
            pnl = float(entry_price) - float(price)
            if isinstance(pnl, (int, float)):
                trades.append(pnl)
            position = None
# -------------------- SYGNAŁ AKTUALNY --------------------
latest_rsi = df["RSI"].dropna().iloc[-1]
latest_macdh = df["MACD_hist"].dropna().iloc[-1]
prev_macdh = df["MACD_hist"].dropna().iloc[-2]
signal = "⏸ BRAK SYGNAŁU"

if position is None:
    if latest_rsi < 30 and prev_macdh < 0 and latest_macdh > 0:
        signal = "🟢 WEJDŹ LONG"
    elif latest_rsi > 70 and prev_macdh > 0 and latest_macdh < 0:
        signal = "🔻 WEJDŹ SHORT"
else:
    if position == "LONG" and (latest_rsi > 60 or latest_macdh < 0):
        signal = "🔴 WYJDŹ z LONG"
    elif position == "SHORT" and (latest_rsi < 50 or latest_macdh > 0):
        signal = "🔴 WYJDŹ z SHORT"
    else:
        signal = f"🕐 TRZYMAJ {position}"

# -------------------- STATYSTYKI --------------------
total = len(trades)
wins = len([t for t in trades if isinstance(t, (int, float)) and t > 0])
losses = len([t for t in trades if isinstance(t, (int, float)) and t <= 0])
skutecznosc = round((wins / total) * 100, 2) if total > 0 else 0
sredni_zysk = round(float(sum(trades)) / total, 2) if total > 0 else 0
laczny_zysk = round(float(sum(trades)), 2)

# -------------------- WYSWIETLANIE --------------------
st.metric("Aktualny sygnał", signal)
st.metric("RSI", round(latest_rsi, 2))
st.metric("MACD Histogram", round(latest_macdh, 2))

st.subheader("📈 Wykres ceny")
fig, ax = plt.subplots()
df["Close"].plot(ax=ax, label="Close Price")
ax.legend()
st.pyplot(fig)

st.subheader("📊 Statystyki strategii")
st.write(f"Ilość pozycji: {total}")
st.write(f"Trafione: {wins}, Nietrafione: {losses}")
st.write(f"Skuteczność: {skutecznosc}%")
st.write(f"Średni wynik na pozycji: {sredni_zysk}")
st.write(f"Łączny wynik: {laczny_zysk}")

