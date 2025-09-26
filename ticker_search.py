"""Utilities for ticker lookup and logo retrieval."""
from __future__ import annotations

import base64
import logging
from functools import lru_cache
from typing import Optional

import requests
import yfinance as yf

LOGGER = logging.getLogger(__name__)


def _extract_domain(website: Optional[str]) -> Optional[str]:
    if not website:
        return None
    clean = website.replace("https://", "").replace("http://", "")
    clean = clean.split("/")[0]
    return clean or None


@lru_cache(maxsize=256)
def _download_image(url: str) -> Optional[bytes]:
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith(
            "image"
        ):
            return response.content
    except Exception as exc:  # noqa: BLE001 - network errors should not crash
        LOGGER.debug("Failed to download image %s: %s", url, exc)
    return None


def _resolve_logo(domain: Optional[str], fallback_url: Optional[str]) -> Optional[bytes]:
    if domain:
        data = _download_image(f"https://logo.clearbit.com/{domain}")
        if data:
            return data
    if fallback_url:
        data = _download_image(fallback_url)
        if data:
            return data
    return None


def _format_suggestion(item: dict) -> dict:
    symbol = item["symbol"]
    name = item["shortname"]
    price = item.get("regularMarketPrice")
    currency = item.get("currency", "")
    website = item.get("website")
    domain = _extract_domain(website)
    fallback_logo_url = item.get("logo_url")

    if domain is None or price is None:
        try:
            info = yf.Ticker(symbol).info
            website = info.get("website") or website
            domain = domain or _extract_domain(website)
            price = info.get("regularMarketPrice", price)
            currency = currency or info.get("currency", "")
            fallback_logo_url = fallback_logo_url or info.get("logo_url")
        except Exception as exc:  # noqa: BLE001 - tolerate yfinance failures
            LOGGER.debug("Failed to enrich ticker %s: %s", symbol, exc)

    logo_bytes = _resolve_logo(domain, fallback_logo_url)

    label_bits = [f"{name} ({symbol})"]
    if price is not None:
        price_str = f"{price:.2f} {currency}".strip()
        label_bits.append(price_str)

    return {
        "label": " - ".join([bit for bit in label_bits if bit]),
        "symbol": symbol,
        "logo_bytes": logo_bytes,
        "logo_data_url": (
            f"data:image/png;base64,{base64.b64encode(logo_bytes).decode('ascii')}"
            if logo_bytes
            else None
        ),
    }


def search_tickers(query: str, *, limit: int = 10) -> list[dict]:
    if not query:
        return []

    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        matches = response.json().get("quotes", [])
    except Exception as exc:  # noqa: BLE001 - degrade gracefully offline
        LOGGER.warning("Ticker search failed for %s: %s", query, exc)
        return []

    suggestions = []
    for item in matches:
        if "symbol" not in item or "shortname" not in item:
            continue
        suggestions.append(_format_suggestion(item))
        if len(suggestions) >= limit:
            break
    return suggestions
