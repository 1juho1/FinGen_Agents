import yfinance as yf
from trading_env import TradingEnv
from stable_baselines3 import PPO
import numpy as np

# Load 1 year of closing prices for a stock (e.g., Tesla)
prices = yf.Ticker("TSLA").history(period="1y")["Close"].dropna().values
prices = np.nan_to_num(prices)

# Create the environment
env = TradingEnv(prices)

# Create and train the PPO model
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

# Save model for later use
model.save("trader_model")

# Print basic summary
print("✅ Training complete. Model saved as trader_model.zip")
