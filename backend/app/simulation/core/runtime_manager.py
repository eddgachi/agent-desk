"""
Runtime manager — holds live MemoryManager and HybridDecisionEngine
instances per agent per simulation.

These objects are not stored in the Pydantic model (they contain
dataclasses and async capabilities). They are serialized into
the Agent model dict fields for transport to the frontend.
"""

import logging
from typing import Dict, Optional

from app.config import settings
from app.simulation.decisions.engine import HybridDecisionEngine
from app.simulation.llm.client import DeepSeekClient
from app.simulation.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class RuntimeManager:
    """
    Holds all runtime objects for a single simulation.
    One instance per SimulationState, created on init.
    """

    def __init__(self, sim_id: str):
        self.sim_id = sim_id

        # Agent memory managers: agent_id → MemoryManager
        self.memory: Dict[str, MemoryManager] = {}

        # Agent decision engines: agent_id → HybridDecisionEngine
        self.decisions: Dict[str, HybridDecisionEngine] = {}

        # LLM client (shared across agents)
        self.llm_client: Optional[DeepSeekClient] = None

    def initialize_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
    ) -> None:
        """Create memory manager and decision engine for an agent."""
        # Memory
        if agent_id not in self.memory:
            self.memory[agent_id] = MemoryManager(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_role=agent_role,
            )

        # Decision engine
        if agent_id not in self.decisions:
            engine = HybridDecisionEngine(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_role=agent_role,
                llm_client=self.llm_client,
                use_llm=False,  # starts without LLM; enabled if configured
            )
            self.decisions[agent_id] = engine

            # If LLM is globally enabled and we have a client, enable it
            if settings.LLM_ENABLED and self.llm_client:
                engine.enable_llm(self.llm_client)

    def setup_llm(self) -> None:
        """Create the shared LLM client if configured."""
        if settings.DEEPSEEK_API_KEY:
            self.llm_client = DeepSeekClient(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model=settings.DEEPSEEK_MODEL,
            )
            logger.info(
                "LLM client created for sim %s (model=%s)",
                self.sim_id, settings.DEEPSEEK_MODEL,
            )
        else:
            logger.info(
                "No DEEPSEEK_API_KEY set — LLM features disabled for sim %s",
                self.sim_id,
            )

    def sync_to_agents(self, agents: Dict) -> None:
        """
        Serialize runtime memory and decision data back into
        the Agent Pydantic models for transport to frontend.
        """
        for agent_id, agent in agents.items():
            mem = self.memory.get(agent_id)
            dec = self.decisions.get(agent_id)

            if mem:
                agent.working_memory = mem.working.to_dict_list()
                agent.episodic_memory = mem.episodic.to_dict_list()
                agent.semantic_memory = mem.semantic.to_dict()
                agent.memory_last_consolidation = mem._last_consolidation_tick

                # Also fill the legacy memory field with recent working memory strings
                agent.memory = [
                    wm.to_short_str()
                    for wm in mem.working.recent(10)
                ]

            if dec:
                explanation = dec.last_explanation
                if explanation:
                    agent.llm_explanation = explanation.get("explanation")
                    agent.llm_feeling = explanation.get("feeling")
                    agent.llm_next_plan = explanation.get("next_plan")

    def get_memory(self, agent_id: str) -> Optional[MemoryManager]:
        return self.memory.get(agent_id)

    def get_decisions(self, agent_id: str) -> Optional[HybridDecisionEngine]:
        return self.decisions.get(agent_id)

    def close(self) -> None:
        """Clean up resources."""
        if self.llm_client:
            import asyncio
            try:
                asyncio.create_task(self.llm_client.close())
            except Exception:
                pass


# Store of runtime managers per simulation
_runtime_store: Dict[str, RuntimeManager] = {}


def get_runtime(sim_id: str) -> RuntimeManager:
    if sim_id not in _runtime_store:
        _runtime_store[sim_id] = RuntimeManager(sim_id)
        _runtime_store[sim_id].setup_llm()
    return _runtime_store[sim_id]


def clear_runtime(sim_id: str) -> None:
    rt = _runtime_store.pop(sim_id, None)
    if rt:
        rt.close()
