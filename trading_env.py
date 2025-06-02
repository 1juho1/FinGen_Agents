import gym
from gym import spaces
import numpy as np

class TradingEnv(gym.Env):
    def __init__(self, prices, initial_balance=1000):
        super().__init__()
        self.prices = prices
        self.initial_balance = initial_balance
        self.action_space = spaces.Discrete(3)  # 0: Hold, 1: Buy, 2: Sell
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(2,), dtype=np.float32)

    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.holding = 0
        return self._get_obs()

    def _get_obs(self):
        return np.array([self.prices[self.current_step], self.holding], dtype=np.float32)

    def step(self, action):
        price = self.prices[self.current_step]
        reward = 0

        if action == 1 and self.balance >= price:  # Buy
            self.balance -= price
            self.holding += 1
        elif action == 2 and self.holding > 0:     # Sell
            self.balance += price
            self.holding -= 1
            reward += price

        self.current_step += 1
        done = self.current_step >= len(self.prices) - 1
        return self._get_obs(), reward, done, {}

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance}, Holding: {self.holding}")
