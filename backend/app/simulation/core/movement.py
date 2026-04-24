import math

from app.simulation.core.event_logger import add_event
from app.simulation.models.simulation_state import Agent, AgentStatus

# Canvas dimensions agents move within
CANVAS_W = 900
CANVAS_H = 620
SPEED = 18.0  # units per tick (canvas-space pixels)

# Wander regions mapped to rooms (agents prefer to stay in the work floor)
WANDER_ZONES = [
    (30, 30, 580, 400),  # work floor (weight 6)
    (30, 30, 580, 400),
    (30, 30, 580, 400),
    (30, 30, 580, 400),
    (30, 30, 580, 400),
    (30, 30, 580, 400),
    (614, 30, 874, 200),  # meeting room A
    (614, 230, 874, 400),  # meeting room B
    (30, 434, 308, 594),  # break room
]


def move_agent_towards_target(agent: Agent, state, rng) -> bool:
    """Move agent one step toward its target. Returns True if arrived."""
    if agent.target_x is None or agent.target_y is None:
        agent.status = AgentStatus.IDLE
        return True

    dx = agent.target_x - agent.position_x
    dy = agent.target_y - agent.position_y
    distance = math.hypot(dx, dy)

    if distance <= SPEED:
        agent.position_x = agent.target_x
        agent.position_y = agent.target_y
        agent.target_x = None
        agent.target_y = None
        return True

    ratio = SPEED / distance
    agent.position_x += dx * ratio
    agent.position_y += dy * ratio
    return False


def choose_wander_target(agent: Agent, rng) -> tuple:
    """Pick a random wander destination within a weighted set of zones."""
    zone = rng.choice(WANDER_ZONES)
    x1, y1, x2, y2 = zone
    tx = rng.randint(int(x1), int(x2))
    ty = rng.randint(int(y1), int(y2))
    return float(tx), float(ty)


def choose_random_wander_target(agent: Agent, rng, bounds=(0, 100)):
    """Legacy alias kept for compatibility."""
    return choose_wander_target(agent, rng)
