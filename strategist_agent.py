import os
from openai import OpenAI

# === Load API Key and Initialize Client ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing from your environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_strategy(advice_text: str, risk_profile: str = "moderate") -> str:
    """
    Generates a portfolio recommendation (Buy, Hold, or Sell) based on 
    an analyst report and the investor's risk profile.
    
    Args:
        advice_text (str): Analyst summary text.
        risk_profile (str): Risk tolerance ("conservative", "moderate", "aggressive").

    Returns:
        str: AI-generated recommendation with rationale and adjustment advice.
    """
    prompt = f"""
You are a portfolio strategist AI.

Based on the following analyst report and the user's risk profile, provide:
1. A recommendation (Buy, Hold, or Sell)
2. A one-paragraph justification
3. Suggested portfolio adjustment (e.g., reduce position by 20%)

Analyst Report:
{advice_text}

Investor Risk Profile: {risk_profile}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4o"
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Error from Strategist Agent:", e)
        return "⚠️ Error: Unable to generate a strategy recommendation at this time."
