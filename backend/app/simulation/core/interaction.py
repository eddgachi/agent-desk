"""
Phase 6: Multi-agent coordination.

Handles:
  - Spontaneous conversations between nearby idle agents
  - Meeting task coordination (all assigned agents must check in)
  - Break triggers based on energy levels
  - Stat decay (energy, focus, mood)
"""

import math

from app.simulation.core.event_logger import add_event
from app.simulation.models.simulation_state import (
    AgentStatus,
    SimulationState,
    TaskStatus,
)

# ── Tuning constants ───────────────────────────────────────
CHAT_TRIGGER_DIST = 60  # px — agents within this range may chat
CHAT_CHANCE = 0.06  # probability per tick
CHAT_DURATION_MIN = 3
CHAT_DURATION_MAX = 7

ENERGY_DECAY_WORKING = 1.2  # per tick while working
ENERGY_DECAY_MEETING = 0.8
ENERGY_DECAY_IDLE = 0.3
ENERGY_RECOVERY_BREAK = 4.0

FOCUS_DECAY_WORKING = 0.8
FOCUS_RECOVERY_BREAK = 2.0
FOCUS_RECOVERY_IDLE = 0.3

MOOD_BOOST_CHAT = 3.0
MOOD_BOOST_TASK_DONE = 5.0
MOOD_DECAY_IDLE_LONG = 0.2

BREAK_THRESHOLD = 20.0  # energy below this → agent heads to break
BREAK_COOLDOWN_TICKS = 30  # minimum ticks between breaks

BREAK_ROOM = [160.0, 510.0]


# ── Public API called from engine ─────────────────────────


def process_stat_decay(state: SimulationState, rng) -> None:
    """Decay energy/focus each tick based on status."""
    for agent in state.agents.values():
        if agent.status == AgentStatus.WORKING:
            agent.energy = max(0.0, agent.energy - ENERGY_DECAY_WORKING)
            agent.focus = max(0.0, agent.focus - FOCUS_DECAY_WORKING)
        elif agent.status == AgentStatus.MEETING:
            agent.energy = max(0.0, agent.energy - ENERGY_DECAY_MEETING)
        elif agent.status in (AgentStatus.BREAK,):
            agent.energy = min(100.0, agent.energy + ENERGY_RECOVERY_BREAK)
            agent.focus = min(100.0, agent.focus + FOCUS_RECOVERY_BREAK)
        elif agent.status == AgentStatus.IDLE:
            agent.energy = max(0.0, agent.energy - ENERGY_DECAY_IDLE)
            agent.focus = min(100.0, agent.focus + FOCUS_RECOVERY_IDLE)


def process_breaks(state: SimulationState, rng) -> None:
    """Send exhausted agents to the break room."""
    for agent in state.agents.values():
        if agent.status in (AgentStatus.BREAK, AgentStatus.MOVING):
            continue
        if agent.energy > BREAK_THRESHOLD:
            continue
        cooldown_ok = (
            state.current_tick - agent.last_break_tick
        ) >= BREAK_COOLDOWN_TICKS
        if not cooldown_ok:
            continue

        # Drop current task
        if agent.current_task_id:
            task = state.tasks.get(agent.current_task_id)
            if task and task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.ASSIGNED  # put back for reassignment
                task.assigned_agent_id = None
            agent.current_task_id = None
            agent.remaining_task_ticks = None

        # Head to break room
        agent.target_x, agent.target_y = BREAK_ROOM
        agent.status = AgentStatus.MOVING
        agent.last_break_tick = state.current_tick

        add_event(
            state,
            "break_started",
            {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "energy": round(agent.energy, 1),
            },
        )


def process_break_arrival(state: SimulationState) -> None:
    """Agents that arrive at break room switch to BREAK status."""
    for agent in state.agents.values():
        if agent.status != AgentStatus.MOVING:
            continue
        if agent.target_x is None:
            continue
        bx, by = BREAK_ROOM
        dist = math.hypot(agent.position_x - bx, agent.position_y - by)
        if dist <= 15 and agent.current_task_id is None:
            # Arrived at break room with no task → start break
            agent.status = AgentStatus.BREAK


def process_break_end(state: SimulationState, rng) -> None:
    """End break when energy is sufficiently restored."""
    for agent in state.agents.values():
        if agent.status != AgentStatus.BREAK:
            continue
        if agent.energy >= 70.0:
            agent.status = AgentStatus.IDLE
            add_event(
                state,
                "break_ended",
                {
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "energy": round(agent.energy, 1),
                },
            )
            # Head back to their desk
            if agent.desk_x is not None:
                agent.target_x = agent.desk_x
                agent.target_y = agent.desk_y
                agent.status = AgentStatus.MOVING


def process_conversations(state: SimulationState, rng) -> None:
    """Spontaneous chat between nearby idle agents."""
    idle_agents = [
        a
        for a in state.agents.values()
        if a.status == AgentStatus.IDLE and a.conversation_partner_id is None
    ]

    paired = set()
    for i, a1 in enumerate(idle_agents):
        if a1.id in paired:
            continue
        for a2 in idle_agents[i + 1 :]:
            if a2.id in paired:
                continue
            dist = math.hypot(
                a1.position_x - a2.position_x, a1.position_y - a2.position_y
            )
            if dist > CHAT_TRIGGER_DIST:
                continue
            if rng.random() > CHAT_CHANCE:
                continue

            # Start conversation
            duration = rng.randint(CHAT_DURATION_MIN, CHAT_DURATION_MAX)
            a1.status = AgentStatus.CHATTING
            a2.status = AgentStatus.CHATTING
            a1.conversation_partner_id = a2.id
            a2.conversation_partner_id = a1.id
            a1.conversation_ticks_left = duration
            a2.conversation_ticks_left = duration

            paired.add(a1.id)
            paired.add(a2.id)

            add_event(
                state,
                "chat_started",
                {
                    "agent_ids": [a1.id, a2.id],
                    "agent_names": [a1.name, a2.name],
                    "agent_name": f"{a1.name} & {a2.name}",
                    "duration": duration,
                },
            )
            break


def process_conversation_tick(state: SimulationState, rng) -> None:
    """Advance ongoing conversations."""
    for agent in state.agents.values():
        if agent.status != AgentStatus.CHATTING:
            continue
        agent.conversation_ticks_left -= 1
        agent.mood = min(100.0, agent.mood + MOOD_BOOST_CHAT * 0.2)

        if agent.conversation_ticks_left <= 0:
            partner = state.agents.get(agent.conversation_partner_id or "")
            agent.status = AgentStatus.IDLE
            agent.conversation_partner_id = None
            agent.conversation_ticks_left = 0

            if partner and partner.status == AgentStatus.CHATTING:
                partner.status = AgentStatus.IDLE
                partner.conversation_partner_id = None
                partner.conversation_ticks_left = 0
                add_event(
                    state,
                    "chat_ended",
                    {
                        "agent_ids": [agent.id, partner.id],
                        "agent_names": [agent.name, partner.name],
                        "agent_name": f"{agent.name} & {partner.name}",
                    },
                )


def process_meeting_checkin(state: SimulationState) -> None:
    """
    When an agent arrives at a meeting-task location, mark them as checked in.
    When all expected participants have checked in, start the meeting countdown.
    """
    for task in state.tasks.values():
        if task.type != "meeting":
            continue
        if task.status not in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
            continue
        if not task.required_location:
            continue

        mx, my = task.required_location
        for agent in state.agents.values():
            if agent.current_task_id != task.id:
                continue
            if agent.id in task.checked_in_agent_ids:
                continue
            dist = math.hypot(agent.position_x - mx, agent.position_y - my)
            if dist <= 20:
                task.checked_in_agent_ids.append(agent.id)
                agent.status = AgentStatus.MEETING

        # If at least one participant has checked in, start the meeting
        if task.checked_in_agent_ids and task.status == TaskStatus.ASSIGNED:
            task.status = TaskStatus.IN_PROGRESS
            task.remaining_ticks = task.duration_ticks
            add_event(
                state,
                "meeting_started",
                {
                    "task_id": task.id,
                    "task_title": task.title,
                    "agent_ids": list(task.checked_in_agent_ids),
                    "agent_name": ", ".join(
                        state.agents[aid].name
                        for aid in task.checked_in_agent_ids
                        if aid in state.agents
                    ),
                },
            )
