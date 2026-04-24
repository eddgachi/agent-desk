import math

from app.simulation.core.event_logger import add_event
from app.simulation.models.simulation_state import Agent, AgentStatus

SPEED = 5.0  # units per tick


def move_agent_towards_target(agent: Agent, state, rng) -> bool:
    if agent.target_x is None or agent.target_y is None:
        return True  # arrived (no target)

    dx = agent.target_x - agent.position_x
    dy = agent.target_y - agent.position_y
    distance = math.hypot(dx, dy)

    if distance <= SPEED:
        # Arrived
        agent.position_x = agent.target_x
        agent.position_y = agent.target_y
        agent.target_x = None
        agent.target_y = None
        agent.status = AgentStatus.IDLE
        add_event(
            state,
            "agent_stopped_moving",
            {"agent_id": agent.id, "position": [agent.position_x, agent.position_y]},
        )
        return True
    else:
        # Move towards
        ratio = SPEED / distance
        agent.position_x += dx * ratio
        agent.position_y += dy * ratio
        return False


def choose_random_wander_target(agent: Agent, rng, bounds=(0, 100)):
    # pick random point within bounds, within 20 units of current position
    from_x = max(bounds[0], agent.position_x - 20)
    to_x = min(bounds[1], agent.position_x + 20)
    from_y = max(bounds[0], agent.position_y - 20)
    to_y = min(bounds[1], agent.position_y + 20)
    target_x = rng.randint(int(from_x), int(to_x))
    target_y = rng.randint(int(from_y), int(to_y))
    return target_x, target_y
