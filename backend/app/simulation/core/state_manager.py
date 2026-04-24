"""
In-memory simulation state store + tick loop with WebSocket broadcasting.
All simulation state lives here during a server session.
"""

import asyncio
import uuid
from typing import Dict, Optional

from app.simulation.core.engine import process_tick
from app.simulation.core.event_logger import add_event
from app.simulation.core.random_gen import clear_rng, get_rng
from app.simulation.core.runtime_manager import clear_runtime, get_runtime
from app.simulation.core.serializers import serialize_event, serialize_tick_update
from app.simulation.core.ws_manager import ws_manager
from app.simulation.models.simulation_state import (
    Agent,
    AgentStatus,
    SimulationState,
    Task,
)

# ── In-memory stores ───────────────────────────────────────
_state_store: Dict[str, SimulationState] = {}
_loop_tasks: Dict[str, asyncio.Task] = {}
_loop_flags: Dict[str, bool] = {}

# ── Agent definitions (canvas-space coordinates) ───────────
# Desk centres from officeLayout.js:
#   makeDeskRow(60, 70, 4, 'A')  → centres at (100,96),(228,96),(356,96),(484,96)
#   makeDeskRow(60, 170, 4, 'B') → centres at (100,196),(228,196),(356,196),(484,196)
_AGENT_DEFS = [
    ("agent_alice", "Alice", "engineer", 100.0, 96.0, "desk_A1"),
    ("agent_bob", "Bob", "designer", 228.0, 96.0, "desk_A2"),
    ("agent_charlie", "Charlie", "manager", 356.0, 96.0, "desk_A3"),
    ("agent_diana", "Diana", "engineer", 484.0, 96.0, "desk_A4"),
    ("agent_eve", "Eve", "analyst", 100.0, 196.0, "desk_B1"),
    ("agent_frank", "Frank", "designer", 228.0, 196.0, "desk_B2"),
]

# Meeting room centres
_MEETING_A = [744.0, 120.0]
_MEETING_B = [744.0, 313.0]


# ── Task catalogue ─────────────────────────────────────────
def _make_tasks() -> Dict[str, Task]:
    """Generate a rich set of initial tasks."""
    defs = [
        # (id, title, desc, type, duration, location, role, priority, deadline_offset)
        (
            "task_sprint_plan",
            "Sprint Planning",
            "Plan the upcoming sprint with the team",
            "meeting",
            12,
            _MEETING_A,
            None,
            5,
            60,
        ),
        (
            "task_code_review",
            "Code Review",
            "Review open pull requests",
            "review",
            8,
            None,
            "engineer",
            4,
            80,
        ),
        (
            "task_design_mockup",
            "UI Mockups",
            "Design mockups for the new dashboard",
            "work",
            14,
            None,
            "designer",
            4,
            90,
        ),
        (
            "task_research",
            "Tech Research",
            "Research suitable database migration strategy",
            "research",
            10,
            None,
            "analyst",
            3,
            None,
        ),
        (
            "task_arch_review",
            "Architecture Review",
            "Review and document system architecture",
            "meeting",
            8,
            _MEETING_B,
            "manager",
            3,
            100,
        ),
        (
            "task_bug_triage",
            "Bug Triage",
            "Review and prioritize open bug reports",
            "review",
            6,
            None,
            "engineer",
            3,
            70,
        ),
        (
            "task_analytics",
            "Analytics Report",
            "Compile and analyse this week's usage data",
            "work",
            12,
            None,
            "analyst",
            2,
            None,
        ),
        (
            "task_onboarding",
            "Onboarding Docs",
            "Update onboarding documentation",
            "work",
            9,
            None,
            None,
            2,
            None,
        ),
        (
            "task_1on1",
            "1-on-1 Meeting",
            "Manager check-ins with team members",
            "meeting",
            6,
            _MEETING_B,
            "manager",
            2,
            None,
        ),
        (
            "task_refactor",
            "Refactoring",
            "Clean up the authentication module",
            "work",
            15,
            None,
            "engineer",
            1,
            None,
        ),
    ]

    tasks = {}
    for tid, title, desc, ttype, dur, loc, role, pri, dl_offset in defs:
        deadline = None if dl_offset is None else dl_offset
        tasks[tid] = Task(
            id=tid,
            title=title,
            description=desc,
            type=ttype,
            duration_ticks=dur,
            required_location=loc,
            required_role=role,
            priority=pri,
            deadline_tick=deadline,
        )
    return tasks


# ── Public API ─────────────────────────────────────────────


def create_simulation(seed: int) -> SimulationState:
    sim_id = str(uuid.uuid4())
    rng = get_rng(sim_id, seed)

    agents: Dict[str, Agent] = {}
    for aid, name, role, px, py, desk_id in _AGENT_DEFS:
        agents[aid] = Agent(
            id=aid,
            name=name,
            role=role,
            position_x=px,
            position_y=py,
            status=AgentStatus.IDLE,
            energy=float(rng.randint(75, 100)),
            focus=float(rng.randint(70, 100)),
            mood=float(rng.randint(60, 90)),
            desk_id=desk_id,
            desk_x=px,
            desk_y=py,
        )

    tasks = _make_tasks()
    state = SimulationState(sim_id=sim_id, agents=agents, tasks=tasks, seed=seed)
    _state_store[sim_id] = state

    # ── Phase 7/9: Initialize runtime memory & decisions ──
    rt = get_runtime(sim_id)
    for aid, name, role, _, _, _ in _AGENT_DEFS:
        rt.initialize_agent(aid, name, role)
    rt.sync_to_agents(state.agents)

    add_event(
        state,
        "simulation_created",
        {
            "sim_id": sim_id,
            "seed": seed,
            "agents": [a.name for a in agents.values()],
        },
    )
    return state


def get_simulation(sim_id: str) -> Optional[SimulationState]:
    return _state_store.get(sim_id)


def update_simulation(state: SimulationState) -> None:
    _state_store[state.sim_id] = state


def reset_simulation(sim_id: str) -> Optional[SimulationState]:
    if sim_id not in _state_store:
        return None
    old = _state_store[sim_id]
    stop_auto_loop(sim_id)
    clear_rng(sim_id)
    clear_runtime(sim_id)
    new = create_simulation(old.seed)
    new.sim_id = sim_id  # keep same ID so frontend WS stays connected
    _state_store[sim_id] = new
    return new


def inject_task(sim_id: str, task: Task) -> Optional[Task]:
    state = get_simulation(sim_id)
    if not state:
        return None
    if task.id in state.tasks:
        task.id = f"{task.id}_{uuid.uuid4().hex[:4]}"
    state.tasks[task.id] = task
    add_event(state, "task_injected", {"task_id": task.id, "title": task.title})
    return task


async def apply_tick(sim_id: str) -> int:
    """Process one tick, broadcast WS updates, return new tick number."""
    state = get_simulation(sim_id)
    if not state:
        raise ValueError(f"Simulation not found: {sim_id}")

    rng = get_rng(sim_id, state.seed)
    events_before = len(state.event_log)

    # Reset thinking status
    for agent in state.agents.values():
        agent.is_thinking = False

    process_tick(state, rng)
    update_simulation(state)

    # Broadcast new events
    new_events = state.event_log[events_before:]
    for ev in new_events:
        await ws_manager.broadcast_event(sim_id, serialize_event(ev))

    # Broadcast tick state
    await ws_manager.broadcast_tick(sim_id, serialize_tick_update(state))

    # ── Phase 8/9: Periodic LLM Explanations ──
    if state.current_tick % 15 == 0:
        rt = get_runtime(sim_id)
        for agent in state.agents.values():
            dec = rt.get_decisions(agent.id)
            if dec and dec.use_llm:
                # Set thinking status
                agent.is_thinking = True
                
                # Run explanation in background to not block the simulation
                asyncio.create_task(_run_explanation(sim_id, agent.id))

    return state.current_tick


async def _run_explanation(sim_id: str, agent_id: str):
    rt = get_runtime(sim_id)
    state = get_simulation(sim_id)
    if not rt or not state: return
    
    agent = state.agents.get(agent_id)
    dec = rt.get_decisions(agent_id)
    if not agent or not dec: return
    
    stats = {
        "energy": agent.energy,
        "focus": agent.focus,
        "mood": agent.mood,
        "status": agent.status.value
    }
    
    result = await dec.generate_explanation(sim_id, stats)
    if result:
        agent.llm_explanation = result.get("explanation")
        agent.llm_feeling = result.get("feeling")
        agent.llm_next_plan = result.get("next_plan")
    
    agent.is_thinking = False


# ── Auto-loop ──────────────────────────────────────────────


async def _run_auto_loop(sim_id: str, interval: float) -> None:
    while not _loop_flags.get(sim_id, False):
        await asyncio.sleep(interval)
        try:
            await apply_tick(sim_id)
        except Exception as exc:
            print(f"[auto-loop] error in sim {sim_id}: {exc}")
            break

    state = get_simulation(sim_id)
    if state:
        state.running = False


def start_auto_loop(sim_id: str, interval: float = 1.0) -> None:
    if sim_id in _loop_tasks and not _loop_tasks[sim_id].done():
        return  # already running
    _loop_flags[sim_id] = False
    state = get_simulation(sim_id)
    if state:
        state.running = True
    _loop_tasks[sim_id] = asyncio.create_task(_run_auto_loop(sim_id, interval))


def stop_auto_loop(sim_id: str) -> None:
    _loop_flags[sim_id] = True
    task = _loop_tasks.pop(sim_id, None)
    if task and not task.done():
        task.cancel()
    state = get_simulation(sim_id)
    if state:
        state.running = False
