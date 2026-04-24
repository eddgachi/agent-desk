import uuid
from typing import Dict, Optional

from app.simulation.core.random_gen import clear_rng, get_rng
from app.simulation.models.simulation_state import (
    Agent,
    AgentStatus,
    SimulationState,
    Task,
    TaskStatus,
)

_state_store: Dict[str, SimulationState] = {}


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
    # For Phase 2, just increment tick (engine will do more in Phase 3)
    state.current_tick += 1
    update_simulation(state)
    return state.current_tick
