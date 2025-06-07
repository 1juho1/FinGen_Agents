import yfinance as yf
from trading_env import TradingEnv
from stable_baselines3 import PPO
import numpy as np
import random

# === Helper: Fetch and preprocess data ===
def get_clean_prices(ticker, period="1y"):
    try:
        data = yf.Ticker(ticker).history(period=period)["Close"].dropna().values
        return np.nan_to_num(data) if len(data) > 100 else None
    except:
        return None

# === Multiple Tickers for Better Training ===
tickers = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN", "JPM"]
all_envs = []

for ticker in tickers:
    prices = get_clean_prices(ticker)
    if prices is not None:
        all_envs.append(TradingEnv(prices))

# === Safety check ===
if not all_envs:
    raise ValueError("❌ No valid ticker data found.")

# === Randomly pick one environment per training step ===
class MultiEnvWrapper:
    def __init__(self, envs):
        self.envs = envs
        self.current_env = random.choice(envs)

    def reset(self):
        self.current_env = random.choice(self.envs)
        return self.current_env.reset()

    def step(self, action):
        return self.current_env.step(action)

    def render(self):
        self.current_env.render()

    @property
    def action_space(self):
        return self.current_env.action_space

    @property
    def observation_space(self):
        return self.current_env.observation_space

# === Train Model ===
env = MultiEnvWrapper(all_envs)
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=20000)

# === Save model ===
model.save("trader_model")
print("✅ Training complete. Model saved as trader_model.zip")
