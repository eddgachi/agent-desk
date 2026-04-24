"""
Episodic memory — stores significant events with structured metadata.

Unlike working memory (short-term, high-turnover), episodic memory
retains important events for longer. Entries are created when:
  - A task is completed or failed
  - A conversation starts or ends
  - A meeting occurs
  - A significant state change happens (e.g., energy crisis)

Episodic entries are compressed/consolidated periodically into
semantic summaries (see semantic_memory.py).
"""

# import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EpisodicMemoryEntry:
    tick: int
    type: str  # task_completed | task_failed | chat | meeting | break | milestone
    title: str
    description: str
    agents_involved: List[str] = field(default_factory=list)
    importance: float = 0.5  # computed at creation time
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    consolidated: bool = False  # True when folded into semantic summary

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "agents_involved": self.agents_involved,
            "importance": round(self.importance, 2),
            "tags": self.tags,
            "consolidated": self.consolidated,
        }

    def to_short_str(self) -> str:
        return f"[T{self.tick}] {self.title}"


class EpisodicMemory:
    """
    Long-term episodic store with bounded capacity.
    Old/low-importance entries are automatically pruned.
    """

    DEFAULT_CAPACITY = 100

    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self._entries: List[EpisodicMemoryEntry] = []
        self._capacity = capacity

    # ── Public API ──────────────────────────────────────────

    def add(
        self,
        tick: int,
        type_: str,
        title: str,
        description: str = "",
        agents_involved: Optional[List[str]] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EpisodicMemoryEntry:
        if importance is None:
            importance = self._compute_importance(type_, description)
        entry = EpisodicMemoryEntry(
            tick=tick,
            type=type_,
            title=title,
            description=description,
            agents_involved=agents_involved or [],
            importance=importance,
            tags=tags or self._infer_tags(type_, title),
            metadata=metadata or {},
        )
        self._entries.append(entry)
        self._prune()
        return entry

    def recent(self, n: int = 10) -> List[EpisodicMemoryEntry]:
        return self._entries[-n:]

    def by_type(self, type_: str, n: int = 5) -> List[EpisodicMemoryEntry]:
        filtered = [e for e in self._entries if e.type == type_]
        return filtered[-n:]

    def search(self, query: str, n: int = 5) -> List[EpisodicMemoryEntry]:
        q = query.lower()
        matches = []
        for e in self._entries:
            if q in e.title.lower() or q in e.description.lower():
                matches.append(e)
            elif any(q in tag.lower() for tag in e.tags):
                matches.append(e)
        scored = sorted(matches, key=lambda e: (e.importance, e.tick), reverse=True)
        return scored[:n]

    def important(
        self, threshold: float = 0.7, n: int = 10
    ) -> List[EpisodicMemoryEntry]:
        scored = [e for e in self._entries if e.importance >= threshold]
        scored.sort(key=lambda e: (-e.importance, -e.tick))
        return scored[:n]

    def unconsolidated(self) -> List[EpisodicMemoryEntry]:
        """Return entries not yet consolidated into semantic summaries."""
        return [e for e in self._entries if not e.consolidated]

    def mark_consolidated(self, entries: List[EpisodicMemoryEntry]) -> None:
        ids = {id(e) for e in entries}
        for e in self._entries:
            if id(e) in ids:
                e.consolidated = True

    def consolidate_prompt(self) -> str:
        """Generate a prompt-friendly summary of recent episodic memory."""
        uncons = self.unconsolidated()
        if not uncons:
            return "No new significant events."
        uncons.sort(key=lambda e: -e.tick)
        top = uncons[:20]
        parts = []
        for e in top:
            agents = f" ({', '.join(e.agents_involved)})" if e.agents_involved else ""
            parts.append(f"- T{e.tick}: {e.title}{agents} [{e.type}]")
        return "\n".join(parts)

    @property
    def entries(self) -> List[EpisodicMemoryEntry]:
        return list(self._entries)

    @property
    def size(self) -> int:
        return len(self._entries)

    def to_dict_list(self) -> List[dict]:
        return [e.to_dict() for e in self._entries]

    def from_dict_list(self, entries: List[dict]) -> None:
        self._entries = [EpisodicMemoryEntry(**e) for e in entries]

    # ── Private helpers ─────────────────────────────────────

    def _compute_importance(self, type_: str, description: str) -> float:
        """Heuristic importance based on event type and content length."""
        base = {
            "task_completed": 0.7,
            "task_failed": 0.8,
            "chat": 0.4,
            "meeting": 0.6,
            "break": 0.3,
            "milestone": 0.9,
            "reflection": 0.5,
        }.get(type_, 0.5)

        # Bonus for longer descriptions (more detailed = potentially more significant)
        length_bonus = min(0.2, len(description) / 500 * 0.2)
        return min(1.0, base + length_bonus)

    def _infer_tags(self, type_: str, title: str) -> List[str]:
        tags = [type_]
        priority_keywords = {
            "sprint": "planning",
            "urgent": "urgent",
            "critical": "critical",
            "review": "review",
            "meeting": "collaboration",
            "chat": "social",
        }
        for kw, tag in priority_keywords.items():
            if kw in title.lower():
                tags.append(tag)
        return tags

    def _prune(self) -> None:
        """Remove lowest-importance consolidated entries when over capacity."""
        if len(self._entries) <= self._capacity:
            return

        consolidated = [e for e in self._entries if e.consolidated]
        unconsolidated = [e for e in self._entries if not e.consolidated]

        if len(unconsolidated) >= self._capacity:
            # Keep only the most important unconsolidated
            unconsolidated.sort(key=lambda e: (-e.importance, -e.tick))
            self._entries = unconsolidated[: self._capacity]
            return

        # Keep all unconsolidated, prune from consolidated (lowest importance first)
        consolidated.sort(key=lambda e: (e.importance, -e.tick))
        needed = self._capacity - len(unconsolidated)
        keep = consolidated[-needed:] if needed > 0 else []
        self._entries = unconsolidated + keep
        self._entries.sort(key=lambda e: e.tick)
