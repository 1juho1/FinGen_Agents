import os
from typing import Optional

import streamlit as st
import yfinance as yf
import requests
import matplotlib.pyplot as plt
from run_pipeline import run_agent_pipeline
from test_trader import run_trader_simulation

# === Environment Fixes ===
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

st.set_page_config(page_title="FinGen AI Dashboard", layout="centered")
st.title("🤖 Justin's Finance AI: Autonomous Trading Agent")

# === Session State Defaults ===
st.session_state.setdefault("search_query", "")
st.session_state.setdefault("selected_ticker", None)
st.session_state.setdefault("selected_ticker_label", None)
st.session_state.setdefault("agent_snapshot", None)
st.session_state.setdefault("search_input_raw", st.session_state.get("search_query", ""))


# === Logo Helpers ===
def _extract_domain(website: Optional[str]) -> Optional[str]:
    if not website:
        return None
    clean = website.replace("https://", "").replace("http://", "")
    clean = clean.split("/")[0]
    return clean or None


@st.cache_data(show_spinner=False)
def _download_image(url: str) -> Optional[bytes]:
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image"):
            return response.content
    except Exception:
        return None
    return None


def _get_logo_bytes(domain: Optional[str], fallback_url: Optional[str]) -> Optional[bytes]:
    if domain:
        data = _download_image(f"https://logo.clearbit.com/{domain}")
        if data:
            return data
    if fallback_url:
        data = _download_image(fallback_url)
        if data:
            return data
    return None


# === Fetch Return Data ===
def fetch_returns_plot(ticker, period="5y", freq="Y"):
    data = yf.Ticker(ticker).history(period=period)
    if data.empty:
        return None

    if freq == "Y":
        resampled = data["Close"].resample("Y").last()
        title = "Year-over-Year"
    elif freq == "Q":
        resampled = data["Close"].resample("Q").last()
        title = "Quarter-over-Quarter"
    elif freq == "M":
        resampled = data["Close"].resample("M").last()
        title = "Month-over-Month"
    else:
        return None

    returns = resampled.pct_change().dropna() * 100

    fig, ax = plt.subplots(figsize=(8, 4))
    returns.plot(kind="bar", ax=ax, color="skyblue", edgecolor="black")
    ax.set_title(f"{ticker} {title} Returns")
    ax.set_ylabel("Return (%)")
    ax.set_xlabel("Period")
    ax.grid(True)
    plt.tight_layout()
    return fig

# === Cached Ticker Search ===
@st.cache_data(show_spinner=False)
def search_tickers_live(query):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        matches = response.json().get("quotes", [])
        suggestions = []
        for item in matches:
            if "symbol" in item and "shortname" in item:
                symbol = item["symbol"]
                name = item["shortname"]
                price = item.get("regularMarketPrice")
                currency = item.get("currency", "")
                website = item.get("website")
                domain = _extract_domain(website)
                fallback_logo_url = item.get("logo_url")

                if not domain or price is None:
                    try:
                        info = yf.Ticker(symbol).info
                        website = info.get("website") or website
                        domain = domain or _extract_domain(website)
                        price = info.get("regularMarketPrice", price)
                        currency = currency or info.get("currency", "")
                        fallback_logo_url = fallback_logo_url or info.get("logo_url")
                    except Exception:
                        pass
                logo_bytes = _get_logo_bytes(domain, fallback_logo_url)
                label_bits = [f"{name} ({symbol})"]
                if price is not None:
                    label_bits.append(f"{price:.2f} {currency}".strip())
                suggestions.append(
                    {
                        "label": " - ".join([bit for bit in label_bits if bit]),
                        "symbol": symbol,
                        "logo_bytes": logo_bytes,
                    }
                )
                if len(suggestions) >= 10:
                    break
        return suggestions
    except:
        return []

# === UI Input ===
raw_query = st.text_input(
    "Search for a Company or Ticker",
    value=st.session_state.get("search_query", ""),
    placeholder="Start typing (min 2 characters)...",
    key="search_input_raw",
)

if raw_query != st.session_state.get("search_query", ""):
    st.session_state["search_query"] = raw_query

query = st.session_state["search_query"].strip()
selected_ticker = st.session_state.get("selected_ticker")

results_container = st.container()

if query:
    with results_container:
        if len(query) < 2:
            st.info("Keep typing to see matches (2+ characters).")
        else:
            results = search_tickers_live(query)
            if results:
                st.write("### 📋 Matching Companies")
                for suggestion in results:
                    logo_bytes = suggestion.get("logo_bytes")
                    if logo_bytes:
                        col_logo, col_button = st.columns([1, 6])
                        with col_logo:
                            st.image(logo_bytes, width=40)
                        with col_button:
                            if st.button(suggestion["label"], key=suggestion["symbol"]):
                                st.session_state["selected_ticker"] = suggestion["symbol"]
                                st.session_state["selected_ticker_label"] = suggestion["label"]
                                st.session_state["agent_snapshot"] = None
                                selected_ticker = suggestion["symbol"]
                    else:
                        if st.button(suggestion["label"], key=suggestion["symbol"]):
                            st.session_state["selected_ticker"] = suggestion["symbol"]
                            st.session_state["selected_ticker_label"] = suggestion["label"]
                            st.session_state["agent_snapshot"] = None
                            selected_ticker = suggestion["symbol"]
            else:
                st.warning("No matching companies found.")
else:
    st.info("Start typing to search for a company or ticker.")

# === Risk Profile Select ===
risk = st.selectbox("🎯 Risk Profile", ["conservative", "moderate", "aggressive"])

# === Data Period and Frequency ===
col1, col2 = st.columns(2)
with col1:
    selected_period = st.selectbox("📅 Data Period", ["5y", "10y"])
with col2:
    freq_map = {"Yearly": "Y", "Quarterly": "Q", "Monthly": "M"}
    selected_freq_label = st.selectbox("⏱️ Return Interval", list(freq_map.keys()))
    selected_freq = freq_map[selected_freq_label]

# === Run AI Agents and Trader ===
if selected_ticker:
    ticker_label = st.session_state.get("selected_ticker_label") or selected_ticker
    st.caption(f"Currently selected: {ticker_label}")

    if st.button("🚀 Run AI Agents"):
        with st.spinner("Running Analyst and Strategist Agents..."):
            summary, strategy = run_agent_pipeline(ticker=selected_ticker, risk_profile=risk)

        with st.spinner("Running Trader Simulation..."):
            trader_fig, trader_stats = run_trader_simulation(ticker=selected_ticker)

        returns_fig = fetch_returns_plot(selected_ticker, selected_period, selected_freq)

        st.session_state["agent_snapshot"] = {
            "summary": summary,
            "strategy": strategy,
            "trader_fig": trader_fig,
            "trader_stats": trader_stats,
            "returns_fig": returns_fig,
        }

    snapshot = st.session_state.get("agent_snapshot")
    if snapshot:
        st.subheader("🔎 Analyst Summary")
        st.write(snapshot["summary"])

        st.subheader("📊 Strategist Recommendation")
        st.write(snapshot["strategy"])

        st.subheader("📉 Trader Agent Simulation")
        st.pyplot(snapshot["trader_fig"])

        st.markdown("#### 📊 Performance Summary")
        for label, value in snapshot["trader_stats"].items():
            st.markdown(f"**{label}:** {value}")

        st.subheader("📈 Historical Returns Analysis")
        if snapshot["returns_fig"]:
            st.pyplot(snapshot["returns_fig"])
        else:
            st.error("Not enough historical data to display returns.")
