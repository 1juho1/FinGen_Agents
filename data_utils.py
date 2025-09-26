import logging
from typing import Optional

import numpy as np
import yfinance as yf


def _generate_synthetic_prices(
    *,
    length: int = 252,
    start_price: float = 100.0,
    drift: float = 0.0005,
    volatility: float = 0.02,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Return a simple geometric Brownian motion price series."""
    rng = np.random.default_rng(seed)
    log_returns = rng.normal(loc=drift, scale=volatility, size=length)
    prices = start_price * np.exp(np.cumsum(log_returns))
    return prices.astype(np.float32)


def get_price_series(
    ticker: str,
    *,
    period: str = "1y",
    min_length: int = 100,
    fallback_length: int = 252,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Fetch price history or fall back to a synthetic series when offline."""
    try:
        history = yf.Ticker(ticker).history(period=period)
        close = history.get("Close")
        if close is not None:
            clean = close.dropna()
            if len(clean) >= min_length:
                return np.nan_to_num(clean.to_numpy(dtype=np.float32))
            logging.warning(
                "Ticker %s returned insufficient data (%s points). Using fallback.",
                ticker,
                len(clean),
            )
        else:
            logging.warning("Ticker %s returned no closing prices. Using fallback.", ticker)
    except Exception as exc:  # noqa: BLE001 - catch network/HTTP errors
        logging.warning("Failed to fetch %s from Yahoo Finance: %s", ticker, exc)

    logging.info("Generating synthetic data for %s", ticker)
    fallback_seed = seed if seed is not None else abs(hash(ticker)) % (2**32)
    return _generate_synthetic_prices(length=fallback_length, seed=fallback_seed)
