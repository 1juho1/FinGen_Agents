import logging
import os
import random
from pathlib import Path
from typing import Optional

import gym
import numpy as np
from gymnasium import spaces as gym_spaces
from stable_baselines3 import PPO

from data_utils import get_price_series
from trading_env import TradingEnv

_MPL_CACHE = Path(__file__).resolve().parent / ".matplotlib_cache"
_MPL_CACHE.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CACHE))

logging.basicConfig(level=logging.INFO)


def _build_env_pool(tickers: list[str]) -> list[TradingEnv]:
    envs: list[TradingEnv] = []
    for ticker in tickers:
        prices = get_price_series(ticker, period="1y", min_length=120)
        envs.append(TradingEnv(prices))
    return envs


class MultiEnvWrapper(gym.Env):
    """Sample a fresh environment for every episode to improve robustness."""

    def __init__(self, envs: list[TradingEnv]):
        super().__init__()
        if not envs:
            raise ValueError("❌ No valid ticker data found.")
        self.envs = envs
        self.current_env = random.choice(envs)
        self.action_space = gym_spaces.Discrete(self.current_env.action_space.n)
        low = np.array(self.current_env.observation_space.low, dtype=np.float32)
        high = np.array(self.current_env.observation_space.high, dtype=np.float32)
        self.observation_space = gym_spaces.Box(low=low, high=high, dtype=np.float32)
        self.metadata = getattr(self.current_env, "metadata", {})

    def reset(self):
        self.current_env = random.choice(self.envs)
        return self.current_env.reset()

    def step(self, action):  # noqa: D401 - gym API
        return self.current_env.step(action)

    def render(self):
        self.current_env.render()

    def seed(self, seed=None):
        for env in self.envs:
            if hasattr(env, "seed"):
                env.seed(seed)
        return [seed]


def train_trader_model(
    *,
    tickers: Optional[list[str]] = None,
    total_timesteps: int = 20_000,
    model_path: str = "trader_model.zip",
) -> None:
    """Train the PPO trader and persist it locally."""
    tickers = tickers or ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN", "JPM"]
    env_pool = _build_env_pool(tickers)
    env = MultiEnvWrapper(env_pool)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=total_timesteps)
    save_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    model.save(save_path)
    logging.info("✅ Training complete. Model saved to %s", model_path)


if __name__ == "__main__":
    train_trader_model()
