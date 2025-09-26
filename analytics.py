import base64
import io
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yfinance as yf


def fetch_returns_plot(
    ticker: str,
    *,
    period: str = "5y",
    freq: str = "Y",
) -> Optional[plt.Figure]:
    """Return a Matplotlib figure showing historical returns."""
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
    if returns.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))
    returns.plot(kind="bar", ax=ax, color="skyblue", edgecolor="black")
    ax.set_title(f"{ticker} {title} Returns")
    ax.set_ylabel("Return (%)")
    ax.set_xlabel("Period")
    ax.grid(True)
    plt.tight_layout()
    return fig


def figure_to_data_url(fig: plt.Figure) -> str:
    """Convert a Matplotlib figure into a PNG data URL."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
