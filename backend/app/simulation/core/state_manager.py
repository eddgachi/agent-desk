import asyncio
import uuid
from typing import Dict, Optional

from app.simulation.core.engine import process_tick
from app.simulation.core.random_gen import clear_rng, get_rng
from app.simulation.models.simulation_state import (
    Agent,
    AgentStatus,
    SimulationState,
    Task,
    TaskStatus,
)

_state_store: Dict[str, SimulationState] = {}
_loop_tasks: Dict[str, asyncio.Task] = {}
_loop_stop_flags: Dict[str, bool] = {}


async def _run_auto_loop(sim_id: str, interval_seconds: float):
    while not _loop_stop_flags.get(sim_id, False):
        await asyncio.sleep(interval_seconds)
        # Apply tick (using existing apply_tick)
        try:
            apply_tick(sim_id)
        except Exception as e:
            print(f"Error in auto loop for {sim_id}: {e}")
            break


def start_auto_loop(sim_id: str, interval_seconds: float = 0.5):
    if sim_id in _loop_tasks and not _loop_tasks[sim_id].done():
        return  # already running
    _loop_stop_flags[sim_id] = False
    task = asyncio.create_task(_run_auto_loop(sim_id, interval_seconds))
    _loop_tasks[sim_id] = task


def stop_auto_loop(sim_id: str):
    if sim_id in _loop_tasks:
        _loop_stop_flags[sim_id] = True
        _loop_tasks[sim_id].cancel()
        del _loop_tasks[sim_id]


def create_simulation(seed: int) -> SimulationState:
    sim_id = str(uuid.uuid4())
    rng = get_rng(sim_id, seed)

    # Create agents
    agents = {}
    agent_names = ["Alice", "Bob"]
    roles = ["engineer", "designer"]
    for i, name in enumerate(agent_names):
        x = rng.randint(0, 100)
        y = rng.randint(0, 100)
        agent = Agent(
            id=f"agent_{i}",
            name=name,
            role=roles[i % len(roles)],
            position_x=x,
            position_y=y,
            status=AgentStatus.IDLE,
            assigned_tasks=[],
        )
        agents[agent.id] = agent

    # Create tasks
    tasks = {}
    task_defs = [
        ("T1", "Write report", "Write quarterly report", "work", 10, None, None, 1),
        ("T2", "Review code", "Review pull requests", "work", 5, None, "engineer", 2),
        ("T3", "Team meeting", "Weekly sync", "meeting", 8, (50, 50), None, 3),
    ]
    for tid, title, desc, typ, duration, loc, role, priority in task_defs:
        loc_tuple = tuple(loc) if loc else None
        task = Task(
            id=tid,
            title=title,
            description=desc,
            type=typ,
            duration_ticks=duration,
            required_location=loc_tuple,
            required_role=role,
            priority=priority,
            status=TaskStatus.PENDING,
        )
        tasks[tid] = task

    state = SimulationState(sim_id=sim_id, agents=agents, tasks=tasks, seed=seed)
    _state_store[sim_id] = state
    return state


def get_simulation(sim_id: str) -> Optional[SimulationState]:
    return _state_store.get(sim_id)


def update_simulation(state: SimulationState):
    _state_store[state.sim_id] = state


def reset_simulation(sim_id: str) -> Optional[SimulationState]:
    if sim_id not in _state_store:
        return None
    old_state = _state_store[sim_id]
    clear_rng(sim_id)
    new_state = create_simulation(old_state.seed)
    # Preserve same sim_id? Better to create new? We'll replace with same ID
    new_state.sim_id = sim_id
    _state_store[sim_id] = new_state
    return new_state


def apply_tick(sim_id: str) -> int:
    state = get_simulation(sim_id)
    if not state:
        raise ValueError("Simulation not found")
    rng = get_rng(
        sim_id, state.seed
    )  # note: get_rng requires sim_id and seed; adjust earlier implementation
    # In random_gen.py, we used _rng_store[sim_id] = SeededRNG(seed). Ensure get_rng works.
    state = process_tick(state, rng)
    update_simulation(state)
    return state.current_tick
