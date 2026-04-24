"""
Hybrid decision engine.

Combines rule-based logic with LLM-enhanced decisions.
General flow per call:
  1. Check if LLM budget & rate limits allow a call
  2. If yes: build context from memory, call LLM, validate result
  3. If LLM unavailable/over-budget/invalid: use rule-based fallback
  4. Apply the decision (may modify agent state)
"""

import logging
from typing import Any, Dict, Optional

from app.simulation.decisions.budget import AgentDecisionBudget
from app.simulation.decisions.fallback import (
    fallback_conversation_line,
    fallback_explanation,
    fallback_task_decision,
)
from app.simulation.decisions.validator import validate_decision
from app.simulation.llm.client import DeepSeekClient
from app.simulation.llm.prompts import (
    build_conversation_prompt,
    build_explanation_prompt,
    build_summarization_prompt,
    build_task_planning_prompt,
)
from app.simulation.llm.rate_limiter import rate_limiter
from app.simulation.llm.validators import (
    validate_conversation_line,
    validate_explanation,
    validate_summaries,
    validate_task_decision,
)
from app.utils.metrics import (
    LLM_CALLS_TOTAL,
    LLM_COST_ESTIMATE,
    LLM_DECISIONS_VALID,
    LLM_LATENCY_SECONDS,
)

logger = logging.getLogger(__name__)


class HybridDecisionEngine:
    """
    Per-agent hybrid decision engine.

    Wraps both rule-based and LLM-enhanced decision making.
    Each agent gets its own instance.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        llm_client: Optional[DeepSeekClient] = None,
        use_llm: bool = False,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_role = agent_role
        self._llm = llm_client
        self._use_llm = use_llm
        self._budget = AgentDecisionBudget()
        self._last_explanation: Dict[str, Any] = {}

    # ── Task planning ───────────────────────────────────────

    async def decide_task_action(
        self,
        sim_id: str,
        energy: float,
        focus: float,
        mood: float,
        has_active_task: bool,
        conversation_partner_id: Optional[str],
        current_tick: int,
        last_break_tick: int,
        memory_context: str = "",
    ) -> Dict[str, Any]:
        """
        Decide what to do next: continue working, take break, socialize, or wait.

        Returns a dict with decision, reasoning, and priority_adjustment.
        """
        self._budget.reset_if_needed(current_tick)

        # Try LLM path if available and budget allows
        if self._can_use_llm(sim_id, cost=1.0):
            llm_result = await self._llm_task_planning(
                energy=energy,
                focus=focus,
                mood=mood,
                context=memory_context,
            )

            if llm_result:
                # Validate against simulation rules
                validation = validate_decision(
                    decision=llm_result.get("decision", "wait"),
                    reasoning=llm_result.get("reasoning", ""),
                    agent_id=self.agent_id,
                    agent_role=self.agent_role,
                    agent_energy=energy,
                    agent_focus=focus,
                    agent_status="idle",  # simplified
                    current_task_id="has_task" if has_active_task else None,
                    conversation_partner_id=conversation_partner_id,
                )

                if validation["valid"]:
                    self._budget.spend()
                    rate_limiter.get_budget(sim_id).spend(cost=1.0)
                    LLM_DECISIONS_VALID.labels(sim_id=sim_id, is_valid="true").inc()
                    return llm_result

                LLM_DECISIONS_VALID.labels(sim_id=sim_id, is_valid="false").inc()
                logger.debug(
                    "Agent %s LLM decision '%s' invalid: %s. Using fallback.",
                    self.agent_id,
                    llm_result.get("decision"),
                    validation["reason"],
                )

        # Fallback to rule-based
        return fallback_task_decision(
            agent_id=self.agent_id,
            agent_energy=energy,
            agent_focus=focus,
            agent_mood=mood,
            has_active_task=has_active_task,
            conversation_partner_id=conversation_partner_id,
            current_tick=current_tick,
            last_break_tick=last_break_tick,
        )

    # ── Conversation generation ─────────────────────────────

    async def generate_conversation_line(
        self,
        sim_id: str,
        partner_name: str,
        partner_role: str,
        context: str = "",
    ) -> Dict[str, Any]:
        """Generate a line of dialogue for a conversation."""
        if self._can_use_llm(sim_id, cost=0.5):
            messages = build_conversation_prompt(
                agent_a=self.agent_name,
                role_a=self.agent_role,
                agent_b=partner_name,
                role_b=partner_role,
                recent_context=context,
            )
            result = await self._call_llm_structured(messages)
            validated = validate_conversation_line(result)

            if validated and validated.get("line", "...") != "...":
                rate_limiter.get_budget(sim_id).spend(cost=0.5)
                return validated

        return fallback_conversation_line(
            agent_name=self.agent_name,
            partner_name=partner_name,
            topic=None,
        )

    # ── Memory consolidation ────────────────────────────────

    async def generate_semantic_summaries(
        self,
        sim_id: str,
        recent_episodes: str,
    ) -> list:
        """Generate semantic summaries from recent episodic memory."""
        if self._can_use_llm(sim_id, cost=2.0):
            messages = build_summarization_prompt(
                agent_name=self.agent_name,
                recent_episodes=recent_episodes,
            )
            result = await self._call_llm_structured(messages)
            validated = validate_summaries(result)

            if validated:
                rate_limiter.get_budget(sim_id).spend(cost=2.0)
                return validated

        return []

    # ── Explanation generation ──────────────────────────────

    async def generate_explanation(
        self,
        sim_id: str,
        stats: Dict[str, float],
        recent_actions: str = "",
    ) -> Dict[str, Any]:
        """Generate a natural-language explanation about current state."""
        if self._can_use_llm(sim_id, cost=0.5):
            messages = build_explanation_prompt(
                agent_name=self.agent_name,
                role=self.agent_role,
                recent_actions=recent_actions,
                stats=stats,
            )
            result = await self._call_llm_structured(messages)
            validated = validate_explanation(result)

            if validated and validated.get("explanation"):
                rate_limiter.get_budget(sim_id).spend(cost=0.5)
                self._last_explanation = validated
                return validated

        return fallback_explanation(
            agent_name=self.agent_name,
            role=self.agent_role,
            status=stats.get("status", "idle"),
            energy=stats.get("energy", 100),
            focus=stats.get("focus", 100),
        )

    # ── LLM internals ──────────────────────────────────────

    def _can_use_llm(self, sim_id: str, cost: float = 1.0) -> bool:
        if not self._use_llm or not self._llm:
            return False
        if not self._budget.can_decide():
            return False
        if not rate_limiter.get_budget(sim_id).can_call(cost):
            return False
        return True

    async def _llm_task_planning(
        self,
        energy: float,
        focus: float,
        mood: float,
        context: str = "",
    ) -> Optional[dict]:
        messages = build_task_planning_prompt(
            agent_name=self.agent_name,
            role=self.agent_role,
            stats={"energy": energy, "focus": focus, "mood": mood},
            current_context=context,
        )
        result = await self._call_llm_structured(messages)
        return validate_task_decision(result)

    async def _call_llm_structured(self, messages: list) -> Optional[dict]:
        if not self._llm:
            return None
        
        sim_id = "default" # TODO: Pass sim_id if available or extract from context
        call_type = "structured" # Simplified
        
        with LLM_LATENCY_SECONDS.labels(sim_id=sim_id, call_type=call_type).time():
            try:
                result = await self._llm.chat_structured(messages)
                LLM_CALLS_TOTAL.labels(sim_id=sim_id, agent_id=self.agent_id, call_type=call_type).inc()
                # Rough cost estimate ($0.001 per call as placeholder)
                LLM_COST_ESTIMATE.labels(sim_id=sim_id).inc(0.001)
                return result
            except Exception as exc:
                logger.error(
                    "LLM call failed for agent %s: %s",
                    self.agent_id,
                    exc,
                )
                return None

    # ── Configuration ───────────────────────────────────────

    def enable_llm(self, client: DeepSeekClient) -> None:
        self._llm = client
        self._use_llm = True

    def disable_llm(self) -> None:
        self._use_llm = False

    @property
    def use_llm(self) -> bool:
        return self._use_llm

    @property
    def last_explanation(self) -> Dict[str, Any]:
        return self._last_explanation

    # ── Serialization ───────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "budget": self._budget.to_dict(),
            "use_llm": self._use_llm,
            "last_explanation": self._last_explanation,
        }

    def from_dict(self, data: dict) -> None:
        self._use_llm = data.get("use_llm", False)
        self._last_explanation = data.get("last_explanation", {})
