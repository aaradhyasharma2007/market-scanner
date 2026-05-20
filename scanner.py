import streamlit as st
import yfinance as yf
import pandas as pd
import warnings

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CORE MATH LOGIC (Same as before) ---
def calculate_indicators(df):
    close_prices = df['Close'].squeeze()
    
    df['EMA_20'] = close_prices.ewm(span=20, adjust=False).mean()
    df['EMA_50'] = close_prices.ewm(span=50, adjust=False).mean()
    
    delta = close_prices.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def generate_signal(df):
    if len(df) < 2:
        return "HOLD (Not enough data)", 0.0

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    signal = "HOLD"
    
    if previous['EMA_20'] < previous['EMA_50'] and latest['EMA_20'] > latest['EMA_50']:
        if latest['RSI'] < 70: signal = "🟢 BUY"
    elif previous['EMA_20'] > previous['EMA_50'] and latest['EMA_20'] < latest['EMA_50']:
        signal = "🔴 SELL"
    elif latest['RSI'] > 80:
        signal = "🔴 SELL (Overbought)"

    close_val = latest['Close']
    if isinstance(close_val, pd.Series): close_val = close_val.iloc[0]
    return signal, float(close_val)

# --- WEB APP UI ---
st.set_page_config(page_title="Pro Market Scanner", layout="wide")

st.title("📈 Live Market & Forex Scanner")
st.markdown("Search for any NSE, BSE, or Forex ticker to instantly calculate moving average signals.")

# The Search Bar
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("Enter Ticker (e.g., RELIANCE.NS, TCS.BO, USDINR=X, AAPL)", "RELIANCE.NS").upper()
with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Spacing
    analyze_button = st.button("Analyze Asset")

st.markdown("---")

if analyze_button or search_query:
    try:
        with st.spinner(f"Fetching live data for {search_query}..."):
            ticker = yf.Ticker(search_query)
            # Fetch 5 days of 1-minute data
            df = ticker.history(period="5d", interval="1m")
            
            if df.empty or len(df) < 50:
                st.error(f"Could not find enough 1-minute data for '{search_query}'. Check the spelling or try a different timeframe.")
            else:
                # Do the math
                df = calculate_indicators(df)
                signal, price = generate_signal(df)
                
                # Display Results in big metric boxes
                st.subheader(f"Results for: {search_query}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Current Price", f"{price:,.2f}")
                m2.metric("Trading Signal", signal)
                m3.metric("Current RSI", f"{df['RSI'].iloc[-1]:.2f}")
                
                # Show a mini price chart
                st.markdown("### Recent Price Action (1-Minute Candles)")
                st.line_chart(df['Close'])

    except Exception as e:
        st.error(f"An error occurred: {e}")

st.markdown("---")
st.caption("Remember: NSE tickers end in `.NS`, BSE tickers end in `.BO`. Forex ends in `=X`.")