from analyst_agent import generate_analyst_summary
from strategist_agent import generate_strategy

def run_agent_pipeline(ticker: str = "TSLA", risk_profile: str = "moderate"):
    """
    Executes the full pipeline: Analyst agent summarizes the company,
    and the Strategist agent makes a portfolio recommendation.
    """
    # === Analyst Agent: Generates financial outlook using vector memory ===
    summary = generate_analyst_summary(ticker=ticker, risk_profile=risk_profile)
    print("\n🔎 Analyst Summary:\n", summary)

    # === Strategist Agent: Makes a recommendation based on the summary ===
    strategy = generate_strategy(summary, risk_profile=risk_profile)
    print("\n📊 Strategist Recommendation:\n", strategy)

    return summary, strategy
