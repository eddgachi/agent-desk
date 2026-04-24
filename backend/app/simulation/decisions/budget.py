"""
Per-agent decision budget.

Tracks how many LLM-enhanced decisions an agent can make
per consolidation window. This is a finer-grained budget
on top of the global LLM token budget.
"""


class AgentDecisionBudget:
    """
    Bounded decision budget per agent per window.

    Each agent gets a limited number of LLM-assisted decisions
    within a window (e.g., every 10 ticks). Using an LLM for a
    decision deducts from this budget.
    """

    def __init__(
        self,
        max_decisions_per_window: int = 3,
        window_ticks: int = 20,
    ):
        self._max = max_decisions_per_window
        self._window = window_ticks
        self._used = 0
        self._last_reset_tick = 0

    def can_decide(self) -> bool:
        return self._used < self._max

    def spend(self) -> bool:
        if not self.can_decide():
            return False
        self._used += 1
        return True

    def reset_if_needed(self, current_tick: int) -> None:
        if current_tick - self._last_reset_tick >= self._window:
            self._used = 0
            self._last_reset_tick = current_tick

    @property
    def remaining(self) -> int:
        return self._max - self._used

    @property
    def used(self) -> int:
        return self._used

    def to_dict(self) -> dict:
        return {
            "max_per_window": self._max,
            "used": self._used,
            "remaining": self.remaining,
            "window_ticks": self._window,
        }
