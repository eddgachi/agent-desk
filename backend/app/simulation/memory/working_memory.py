"""
Working memory — short-term context an agent carries between ticks.

Each memory item is a structured record:
  - tick:        simulation tick when this was recorded
  - type:        category (task, chat, movement, observation, decision)
  - content:     human-readable text
  - source:      what triggered it (engine, llm, system)
  - importance:  0.0–1.0 score for pruning/consolidation
  - metadata:    optional structured payload
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkingMemoryItem:
    tick: int
    type: str  # task | chat | movement | observation | decision | reflection
    content: str
    source: str = "engine"  # engine | llm | system
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "type": self.type,
            "content": self.content,
            "source": self.source,
            "importance": round(self.importance, 2),
            "metadata": self.metadata,
        }

    def to_short_str(self) -> str:
        return f"[T{self.tick}] {self.type}: {self.content[:80]}"


class WorkingMemory:
    """
    Bounded, sliding-window working memory.
    Old / low-importance items are pruned when capacity is exceeded.
    """

    DEFAULT_CAPACITY = 30

    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self._items: List[WorkingMemoryItem] = []
        self._capacity = capacity
        self._next_id = 0

    # ── Public API ──────────────────────────────────────────

    def add(
        self,
        tick: int,
        type_: str,
        content: str,
        source: str = "engine",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkingMemoryItem:
        item = WorkingMemoryItem(
            tick=tick,
            type=type_,
            content=content,
            source=source,
            importance=importance,
            metadata=metadata or {},
        )
        self._items.append(item)
        self._prune()
        return item

    def recent(self, n: int = 10) -> List[WorkingMemoryItem]:
        """Return the N most recent items."""
        return self._items[-n:]

    def by_type(self, type_: str, n: int = 5) -> List[WorkingMemoryItem]:
        """Return the N most recent items of a given type."""
        filtered = [it for it in self._items if it.type == type_]
        return filtered[-n:]

    def search(self, query: str, n: int = 3) -> List[WorkingMemoryItem]:
        """
        Simple keyword-based memory retrieval.
        Returns items whose content contains the query (case-insensitive).
        """
        q = query.lower()
        matches = [it for it in self._items if q in it.content.lower()]
        return matches[-n:]

    def consolidate(self, keep_types: Optional[List[str]] = None) -> str:
        """
        Produce a compact text summary of working memory suitable
        for use in LLM prompts. Keeps high-importance + recent items.
        """
        # Score items: recent + high importance
        now = max((it.tick for it in self._items), default=0)
        scored = []
        for it in self._items:
            recency = math.exp(-0.05 * (now - it.tick))  # decay with tick distance
            score = 0.7 * it.importance + 0.3 * recency
            if keep_types and it.type in keep_types:
                score += 0.2
            scored.append((score, it))

        scored.sort(key=lambda x: -x[0])
        top = scored[:15]  # take top 15 for prompt context
        parts = [f"Tick {it.tick} [{it.type}] {it.content}" for _, it in top]
        return "\n".join(parts)

    @property
    def items(self) -> List[WorkingMemoryItem]:
        return list(self._items)

    @property
    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def to_dict_list(self) -> List[dict]:
        return [it.to_dict() for it in self._items]

    def from_dict_list(self, items: List[dict]) -> None:
        self._items = [WorkingMemoryItem(**it) for it in items]

    # ── Private ─────────────────────────────────────────────

    def _prune(self) -> None:
        """Remove lowest-importance items when over capacity."""
        if len(self._items) <= self._capacity:
            return

        # Sort by importance ascending, remove from front
        self._items.sort(key=lambda it: it.importance)
        excess = len(self._items) - self._capacity
        self._items = self._items[excess:]

        # Restore temporal order
        self._items.sort(key=lambda it: it.tick)
