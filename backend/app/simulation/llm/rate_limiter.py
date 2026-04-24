"""
Rate limiter and usage budget tracker for LLM API calls.

Ensures bounded LLM usage per simulation and per agent.
Uses a token-bucket approach: each simulation has a budget
of LLM calls that can be spent across ticks.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class LLMBudget:
    """
    Per-simulation LLM usage budget.

    Budget replenishes at a fixed rate per tick.
    Each LLM call deducts from the budget.
    """

    def __init__(
        self,
        max_budget: int = 50,
        replenish_per_tick: float = 0.5,
        max_agents_per_call: int = 3,
    ):
        self._max_budget = max_budget
        self._budget = float(max_budget)
        self._replenish_per_tick = replenish_per_tick
        self._max_agents_per_call = max_agents_per_call
        self._total_calls = 0
        self._total_tokens = 0

    # ── Public API ──────────────────────────────────────────

    def refresh(self, ticks_elapsed: int = 1) -> None:
        """Replenish budget based on elapsed ticks."""
        self._budget = min(
            self._max_budget,
            self._budget + self._replenish_per_tick * ticks_elapsed,
        )

    def can_call(self, cost: float = 1.0) -> bool:
        """Check if a call can be made within budget."""
        return self._budget >= cost

    def spend(self, cost: float = 1.0, tokens: int = 0) -> bool:
        """
        Spend budget on a call. Returns True if successful.
        """
        if self._budget < cost:
            logger.warning(
                "LLM budget exhausted (budget=%.1f, cost=%.1f)", self._budget, cost
            )
            return False

        self._budget -= cost
        self._total_calls += 1
        self._total_tokens += tokens
        return True

    @property
    def budget_remaining(self) -> float:
        return round(self._budget, 1)

    @property
    def budget_pct(self) -> float:
        """Percentage of budget remaining (0-100)."""
        return round((self._budget / self._max_budget) * 100, 1)

    @property
    def total_calls(self) -> int:
        return self._total_calls

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    def to_dict(self) -> dict:
        return {
            "budget_remaining": self.budget_remaining,
            "budget_pct": self.budget_pct,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
        }


class RateLimiter:
    """
    Per-simulation rate limiter that manages budgets.
    """

    def __init__(self):
        self._budgets: Dict[str, LLMBudget] = {}

    def get_budget(self, sim_id: str) -> LLMBudget:
        if sim_id not in self._budgets:
            self._budgets[sim_id] = LLMBudget()
        return self._budgets[sim_id]

    def refresh_all(self, ticks_elapsed: int = 1) -> None:
        for budget in self._budgets.values():
            budget.refresh(ticks_elapsed)

    def remove(self, sim_id: str) -> None:
        self._budgets.pop(sim_id, None)


# Singleton
rate_limiter = RateLimiter()
