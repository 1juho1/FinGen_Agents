import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from trading_env import TradingEnv  # make sure this file exists in your project

def run_trader_simulation(ticker="TSLA"):
    # === Get 3 months of historical closing prices
    prices = yf.Ticker(ticker).history(period="3mo")["Close"].dropna().values
    prices = np.nan_to_num(prices)

    # === Initialize environment and load model
    env = TradingEnv(prices)
    model = PPO.load("trader_model.zip")
    obs = env.reset()

    # === Run simulation loop
    portfolio_values = []
    buy_steps = []
    sell_steps = []
    trade_log = []
    initial_balance = env.initial_balance

    for step in range(len(prices) - 1):
        action, _ = model.predict(obs.reshape(1, -1), deterministic=True)
        obs, reward, done, _ = env.step(action)

        if action == 1:
            buy_steps.append(step)
            trade_log.append(("Buy", prices[env.current_step]))
        elif action == 2:
            sell_steps.append(step)
            trade_log.append(("Sell", prices[env.current_step]))

        total_value = env.balance + env.holding * prices[env.current_step]
        portfolio_values.append(total_value)

        if done:
            break

    # === Calculate performance
    final_value = portfolio_values[-1] if portfolio_values else initial_balance
    return_pct = ((final_value - initial_balance) / initial_balance) * 100

    stats = {
        "Initial Balance": f"${initial_balance:.2f}",
        "Final Value": f"${final_value:.2f}",
        "Return (%)": f"{return_pct:.2f}%",
        "Total Trades": len(trade_log),
        "Buys": len([t for t in trade_log if t[0] == "Buy"]),
        "Sells": len([t for t in trade_log if t[0] == "Sell"]),
    }

    # === Plot portfolio value and trade points
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(portfolio_values, label="Portfolio Value", linewidth=2)
    ax.scatter(buy_steps, [portfolio_values[i] for i in buy_steps], color="green", marker="^", label="Buy")
    ax.scatter(sell_steps, [portfolio_values[i] for i in sell_steps], color="red", marker="v", label="Sell")
    ax.set_title(f"{ticker} Trader Agent Simulation")
    ax.set_xlabel("Steps")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.close(fig)  # For Streamlit use

    return fig, stats
