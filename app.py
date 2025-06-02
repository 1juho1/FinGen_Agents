import os
import streamlit as st
import yfinance as yf
import requests
from run_pipeline import run_agent_pipeline
from test_trader import run_trader_simulation

# === Environment Fixes ===
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

st.set_page_config(page_title="FinGen AI Dashboard", layout="centered")
st.title("🤖 FinGen AI: Autonomous Trading Agent")

# === Cached Ticker Search ===
@st.cache_data(show_spinner=False)
def search_tickers_live(query):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = data.get("quotes", [])
        suggestions = []
        for item in matches:
            if "symbol" in item and "shortname" in item:
                symbol = item["symbol"]
                name = item["shortname"]
                try:
                    info = yf.Ticker(symbol).info
                    domain = info.get("website", "").replace("https://", "").replace("http://", "").split("/")[0]
                    logo_url = f"https://logo.clearbit.com/{domain}" if domain else "https://via.placeholder.com/40"
                    price = info.get("regularMarketPrice", None)
                    currency = info.get("currency", "")
                    if price is not None:
                        suggestions.append({
                            "label": f"{name} ({symbol}) - {price:.2f} {currency}",
                            "symbol": symbol,
                            "logo": logo_url
                        })
                except:
                    continue
        return suggestions
    except:
        return []

# === UI Input ===
query = st.text_input("Search for a Company or Ticker")
selected_ticker = st.session_state.get("selected_ticker")

if query:
    results = search_tickers_live(query)
    if results:
        st.write("### 📋 Matching Companies")
        for s in results:
            col1, col2 = st.columns([1, 6])
            with col1:
                st.image(s["logo"], width=40)
            with col2:
                if st.button(s["label"], key=s["symbol"]):
                    st.session_state["selected_ticker"] = s["symbol"]
                    selected_ticker = s["symbol"]
    else:
        st.warning("No matching companies found.")
else:
    st.info("Start typing to search for a company or ticker.")

# === Risk Profile ===
risk = st.selectbox("🎯 Risk Profile", ["conservative", "moderate", "aggressive"])

# === Agent + Simulation Run ===
if selected_ticker:
    if st.button("🚀 Run AI Agents"):
        with st.spinner("Running Analyst and Strategist Agents..."):
            summary, strategy = run_agent_pipeline(ticker=selected_ticker, risk_profile=risk)

        st.subheader("🔎 Analyst Summary")
        st.write(summary)

        st.subheader("📊 Strategist Recommendation")
        st.write(strategy)

        with st.spinner("Running Trader Simulation..."):
            fig, stats = run_trader_simulation(ticker=selected_ticker)

        st.subheader("📉 Trader Agent Simulation")
        st.pyplot(fig)

        st.markdown("#### 📊 Performance Summary")
        for label, value in stats.items():
            st.markdown(f"**{label}:** {value}")
