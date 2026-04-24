"""
Memory manager — orchestrates working, episodic, and semantic memory.

Provides a unified API for:
  - Recording events (auto-routed to correct memory type)
  - Retrieving context for LLM prompts
  - Consolidating episodic → semantic summaries
  - Searching across all memory types
"""

import logging
from typing import Dict, List

from app.simulation.memory.episodic_memory import EpisodicMemory
from app.simulation.memory.semantic_memory import SemanticMemory
from app.simulation.memory.working_memory import WorkingMemory

logger = logging.getLogger(__name__)

# How often (in ticks) to trigger semantic consolidation
CONSOLIDATION_INTERVAL = 20


class MemoryManager:
    """Owned by each agent. All memory reads/writes go through here."""

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        working_capacity: int = 30,
        episodic_capacity: int = 100,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_role = agent_role

        self.working = WorkingMemory(capacity=working_capacity)
        self.episodic = EpisodicMemory(capacity=episodic_capacity)
        self.semantic = SemanticMemory()

        # Seed initial self-knowledge
        self.semantic.build_default_self_summary(agent_name, agent_role)

        self._last_consolidation_tick: int = 0

    # ── Recording ───────────────────────────────────────────

    def record_task_assigned(self, tick: int, task_title: str, task_id: str) -> None:
        self.working.add(
            tick,
            "task",
            f"Assigned task: {task_title}",
            source="engine",
            importance=0.6,
            metadata={"task_id": task_id},
        )

    def record_task_started(self, tick: int, task_title: str, task_id: str) -> None:
        self.working.add(
            tick,
            "task",
            f"Started working on: {task_title}",
            source="engine",
            importance=0.7,
            metadata={"task_id": task_id},
        )

    def record_task_completed(
        self, tick: int, task_title: str, task_id: str, task_type: str
    ) -> None:
        self.working.add(
            tick,
            "task",
            f"Completed task: {task_title}",
            source="engine",
            importance=0.8,
            metadata={"task_id": task_id},
        )
        self.episodic.add(
            tick=tick,
            type_="task_completed",
            title=f"Completed '{task_title}'",
            description=f"Finished {task_type} task: {task_title}",
            agents_involved=[self.agent_id],
            importance=0.7,
            tags=[task_type, "task"],
            metadata={"task_id": task_id},
        )

    def record_task_failed(self, tick: int, task_title: str, reason: str) -> None:
        self.working.add(
            tick,
            "task",
            f"Failed task: {task_title} ({reason})",
            source="engine",
            importance=0.9,
            metadata={"reason": reason},
        )
        self.episodic.add(
            tick=tick,
            type_="task_failed",
            title=f"Failed '{task_title}'",
            description=f"Task failed: {task_title}. Reason: {reason}",
            agents_involved=[self.agent_id],
            importance=0.8,
            tags=["failure", "task"],
        )

    def record_chat_started(
        self, tick: int, partner_name: str, partner_id: str
    ) -> None:
        self.working.add(
            tick,
            "chat",
            f"Started chatting with {partner_name}",
            source="engine",
            importance=0.5,
            metadata={"partner_id": partner_id},
        )

    def record_chat_ended(
        self,
        tick: int,
        partner_name: str,
        partner_id: str,
        duration: int = 0,
    ) -> None:
        self.working.add(
            tick,
            "chat",
            f"Chatted with {partner_name} for {duration} ticks",
            source="engine",
            importance=0.5,
            metadata={"partner_id": partner_id, "duration": duration},
        )

    def record_meeting(
        self, tick: int, meeting_title: str, other_agents: List[str]
    ) -> None:
        self.working.add(
            tick,
            "task",
            f"Attended meeting: {meeting_title}",
            source="engine",
            importance=0.7,
            metadata={"meeting_title": meeting_title},
        )
        self.episodic.add(
            tick=tick,
            type_="meeting",
            title=f"Meeting: {meeting_title}",
            description=f"Attended '{meeting_title}' with {', '.join(other_agents)}",
            agents_involved=[self.agent_id] + other_agents,
            importance=0.6,
            tags=["meeting", "collaboration"],
        )

    def record_break(self, tick: int, reason: str = "low_energy") -> None:
        self.working.add(
            tick,
            "movement",
            f"Took a break ({reason})",
            source="engine",
            importance=0.4,
            metadata={"reason": reason},
        )

    def record_observation(
        self, tick: int, content: str, importance: float = 0.3
    ) -> None:
        self.working.add(
            tick,
            "observation",
            content,
            source="system",
            importance=importance,
        )

    def record_decision(
        self,
        tick: int,
        decision: str,
        reasoning: str,
        source: str = "engine",
    ) -> None:
        self.working.add(
            tick,
            "decision",
            f"Decided: {decision}",
            source=source,
            importance=0.6,
            metadata={"reasoning": reasoning},
        )

    # ── Retrieval ──────────────────────────────────────────

    def get_context_for_llm(self, max_working: int = 15) -> str:
        """
        Build a consolidated context string for insertion into an LLM prompt.
        Includes recent working memory, top episodic events, and semantic summaries.
        """
        parts = []

        # 1. Working memory (recent)
        recent_working = self.working.recent(max_working)
        if recent_working:
            parts.append("--- Recent events (working memory) ---")
            for item in reversed(recent_working):
                parts.append(f"  Tick {item.tick} [{item.type}]: {item.content}")
            parts.append("")

        # 2. Episodic memory (important events)
        important_ep = self.episodic.important(threshold=0.6, n=5)
        if important_ep:
            parts.append("--- Important past events ---")
            for ep in important_ep:
                parts.append(f"  T{ep.tick}: {ep.title}")
            parts.append("")

        # 3. Semantic memory (consolidated knowledge)
        semantic_context = self.semantic.to_prompt_context()
        if semantic_context:
            parts.append(semantic_context)
            parts.append("")

        return "\n".join(parts)

    def search(self, query: str, n: int = 5) -> List[dict]:
        """Search across all memory types."""
        results = []
        for m in self.working.search(query, n=n):
            results.append({"type": "working", **m.to_dict()})
        for m in self.episodic.search(query, n=n):
            results.append({"type": "episodic", **m.to_dict()})
        return results

    # ── Consolidation ───────────────────────────────────────

    def maybe_consolidate(self, current_tick: int) -> bool:
        """
        Check if it's time to consolidate episodic → semantic.
        Returns True if consolidation was performed.
        """
        if current_tick - self._last_consolidation_tick < CONSOLIDATION_INTERVAL:
            return False

        unconsolidated = self.episodic.unconsolidated()
        if not unconsolidated:
            self._last_consolidation_tick = current_tick
            return False

        # Group by type for targeted summaries
        by_type: Dict[str, List] = {}
        for entry in unconsolidated:
            by_type.setdefault(entry.type, []).append(entry)

        for type_, entries in by_type.items():
            if len(entries) == 1:
                e = entries[0]
                self.semantic.add(
                    (
                        "work"
                        if type_ in ("task_completed", "task_failed")
                        else "observations"
                    ),
                    f"T{e.tick}: {e.title}",
                    tick=e.tick,
                    confidence=0.6 + 0.3 * e.importance,
                    tags=e.tags,
                )
            else:
                # Multiple entries of same type → aggregate summary
                count = len(entries)
                first = min(e.tick for e in entries)
                last = max(e.tick for e in entries)

                if type_ == "task_completed":
                    task_names = ", ".join(
                        e.title.replace("Completed '", "").rstrip("'")
                        for e in entries[:3]
                    )
                    suffix = f" (and {count - 3} more)" if count > 3 else ""
                    summary = f"Completed {count} tasks between T{first}-T{last}: {task_names}{suffix}"
                    category = "work"
                elif type_ == "task_failed":
                    summary = f"Failed {count} tasks between T{first}-T{last}"
                    category = "work"
                elif type_ == "meeting":
                    summary = f"Attended {count} meetings between T{first}-T{last}"
                    category = "relationships"
                else:
                    summary = f"{count} events ({type_}) between T{first}-T{last}"
                    category = "observations"

                self.semantic.add(
                    category,
                    summary,
                    tick=current_tick,
                    confidence=0.7,
                    tags=[type_],
                )

        self.episodic.mark_consolidated(unconsolidated)
        self._last_consolidation_tick = current_tick
        logger.info(
            "Agent %s: consolidated %d episodic entries at tick %d",
            self.agent_id,
            len(unconsolidated),
            current_tick,
        )
        return True

    # ── Serialization ───────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "working": self.working.to_dict_list(),
            "episodic": self.episodic.to_dict_list(),
            "semantic": self.semantic.to_dict(),
            "last_consolidation_tick": self._last_consolidation_tick,
        }

    def from_dict(self, data: dict) -> None:
        self.working.from_dict_list(data.get("working", []))
        self.episodic.from_dict_list(data.get("episodic", []))
        self.semantic.from_dict(data.get("semantic", {}))
        self._last_consolidation_tick = data.get("last_consolidation_tick", 0)
