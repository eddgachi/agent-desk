import pytest
from app.simulation.core.state_manager import create_simulation, apply_tick, get_simulation
from app.simulation.models.simulation_state import AgentStatus

def test_simulation_initialization():
    seed = 42
    state = create_simulation(seed)
    assert state.seed == seed
    assert len(state.agents) > 0
    assert state.current_tick == 0
    assert state.sim_id is not None

@pytest.mark.asyncio
async def test_tick_progression():
    seed = 123
    state = create_simulation(seed)
    sim_id = state.sim_id
    
    # Process 5 ticks
    for _ in range(5):
        await apply_tick(sim_id)
    
    updated_state = get_simulation(sim_id)
    assert updated_state.current_tick == 5

def test_deterministic_seeding():
    seed = 999
    state1 = create_simulation(seed)
    state2 = create_simulation(seed)
    
    # Check that initial agent stats are identical due to same seed
    for aid in state1.agents:
        a1 = state1.agents[aid]
        a2 = state2.agents[aid]
        assert a1.energy == a2.energy
        assert a1.focus == a2.focus
        assert a1.mood == a2.mood

def test_agent_status_transitions():
    state = create_simulation(42)
    # Initially all agents are IDLE or MOVING (if wander triggered on create)
    # Our create_simulation sets them to IDLE.
    for agent in state.agents.values():
        assert agent.status in (AgentStatus.IDLE, AgentStatus.MOVING)
