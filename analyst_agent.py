import yfinance as yf
import feedparser
import urllib.parse
import os
from openai import OpenAI

# === Load API Key ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing from environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

# === Stock Info ===
def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")
    info = stock.info

    return {
        "name": info.get("longName", ticker),
        "sector": info.get("sector", "N/A"),
        "summary": info.get("longBusinessSummary", "No summary available."),
        "price_data": hist.tail(5)
    }

# === News ===
def get_news(company):
    encoded = urllib.parse.quote(company + " stock")
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={encoded}")
    return [entry['title'] + " - " + entry['link'] for entry in feed.entries[:5]]

# === Analyst Summary ===
def generate_analyst_summary(ticker: str, risk_profile: str):
    data = get_stock_info(ticker)
    news = get_news(data["name"])

    price_str = data["price_data"].to_string()
    news_str = "\n".join(news)

    prompt = f"""
You are a financial analyst AI.

Company: {data['name']}
Sector: {data['sector']}
Risk Profile: {risk_profile}

Business Summary: {data['summary']}

Recent Stock Prices:
{price_str}

Recent News Headlines:
{news_str}

Generate a concise financial outlook with:
1. Trend analysis
2. Key risks
3. Investment insights based on the above data
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4o"
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Error generating summary:", e)
        return "Error: Unable to generate analyst summary."
