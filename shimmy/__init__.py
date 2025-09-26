"""Local shimmy shim for offline compatibility with Stable-Baselines3."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import gym
import gymnasium


class _BaseCompatibility(gymnasium.Env):
    def __init__(self, env: gym.Env):
        super().__init__()
        self.env = env
        self.observation_space = env.observation_space
        self.action_space = env.action_space
        self.metadata = getattr(env, "metadata", {})

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        if seed is not None and hasattr(self.env, "seed"):
            self.env.seed(seed)
        result = self.env.reset()
        if isinstance(result, tuple) and len(result) == 2:
            obs, info = result
        else:
            obs, info = result, {}
        return obs, info

    def step(self, action: Any) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
        result = self.env.step(action)
        if len(result) == 5:
            obs, reward, terminated, truncated, info = result
            return obs, reward, bool(terminated), bool(truncated), info
        obs, reward, done, info = result
        truncated = bool(info.pop("TimeLimit.truncated", False))
        return obs, reward, bool(done), truncated, info

    def render(self, *args, **kwargs):
        return self.env.render(*args, **kwargs)

    def close(self):
        return self.env.close()


class GymV21CompatibilityV0(_BaseCompatibility):
    ...


class GymV26CompatibilityV0(_BaseCompatibility):
    ...


__all__ = ["GymV21CompatibilityV0", "GymV26CompatibilityV0"]
