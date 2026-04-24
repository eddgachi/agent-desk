"""
Semantic memory — consolidated knowledge and summaries.

Periodically, episodic memory entries are "consolidated" into
compact semantic summaries that capture what the agent knows
about:
  - Its work patterns and accomplishments
  - Its relationships with other agents
  - General observations about the office/team

These summaries are used in LLM prompts to provide long-term
context without overwhelming the context window.
"""

# import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SemanticSummary:
    category: str  # self | relationships | work | observations
    content: str
    tick: int
    confidence: float = 0.8  # how reliable/sure this knowledge is
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "content": self.content,
            "tick": self.tick,
            "confidence": round(self.confidence, 2),
            "tags": self.tags,
        }


class SemanticMemory:
    """
    Stores consolidated summaries.
    Each category can have multiple entries (different aspects).
    """

    MAX_PER_CATEGORY = 5

    def __init__(self):
        self._summaries: Dict[str, List[SemanticSummary]] = {
            "self": [],
            "relationships": [],
            "work": [],
            "observations": [],
        }

    # ── Public API ──────────────────────────────────────────

    def add(
        self,
        category: str,
        content: str,
        tick: int,
        confidence: float = 0.8,
        tags: Optional[List[str]] = None,
    ) -> SemanticSummary:
        if category not in self._summaries:
            self._summaries[category] = []

        summary = SemanticSummary(
            category=category,
            content=content,
            tick=tick,
            confidence=confidence,
            tags=tags or [],
        )
        self._summaries[category].append(summary)

        # Prune oldest/lowest-confidence if over max
        self._summaries[category].sort(key=lambda s: (-s.tick, s.confidence))
        if len(self._summaries[category]) > self.MAX_PER_CATEGORY:
            self._summaries[category] = self._summaries[category][
                : self.MAX_PER_CATEGORY
            ]

        return summary

    def get(self, category: str) -> List[SemanticSummary]:
        return list(self._summaries.get(category, []))

    def all(self) -> List[SemanticSummary]:
        result = []
        for cat_list in self._summaries.values():
            result.extend(cat_list)
        result.sort(key=lambda s: -s.tick)
        return result

    def to_prompt_context(self) -> str:
        """Format all semantic memory for insertion into an LLM prompt."""
        parts = []
        for category in ["self", "work", "relationships", "observations"]:
            summaries = self._summaries.get(category, [])
            if not summaries:
                continue
            parts.append(f"=== {category.upper()} ===")
            for s in summaries:
                parts.append(f"  - {s.content}")
        return "\n".join(parts)

    def build_default_self_summary(self, agent_name: str, role: str) -> None:
        """Populate initial self-knowledge when an agent is created."""
        self.add(
            "self",
            f"My name is {agent_name}. I work as a {role} in this office.",
            tick=0,
            confidence=1.0,
            tags=["identity", "role"],
        )

    # ── Serialization ───────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            cat: [s.to_dict() for s in summaries]
            for cat, summaries in self._summaries.items()
        }

    def from_dict(self, data: dict) -> None:
        for cat, summaries in data.items():
            self._summaries[cat] = [SemanticSummary(**s) for s in summaries]
