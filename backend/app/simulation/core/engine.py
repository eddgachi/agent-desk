"""
Core simulation tick processor.
Order of operations per tick:
  1. Stat decay (energy / focus / mood)
  2. Process ongoing conversations (tick down, end if done)
  3. Process meeting check-ins
  4. Move all MOVING agents; handle arrivals
  5. Tick down WORKING agents; handle completions
  6. Check task deadlines
  7. Send exhausted agents to break; end breaks when recovered
  8. Assign pending tasks to eligible idle agents
  9. Initiate spontaneous conversations
  10. Idle agents may wander
  11. Memory consolidation (periodic)
  12. LLM explanation generation (periodic, low priority)
  13. Increment tick counter
"""

import logging

from app.simulation.core.event_logger import add_event
from app.simulation.core.interaction import (
    process_break_arrival,
    process_break_end,
    process_breaks,
    process_conversation_tick,
    process_conversations,
    process_meeting_checkin,
    process_stat_decay,
)
from app.simulation.core.movement import choose_wander_target, move_agent_towards_target
from app.simulation.core.runtime_manager import get_runtime
from app.simulation.core.task_assignment import assign_tasks
from app.simulation.models.simulation_state import (
    AgentStatus,
    SimulationState,
    TaskStatus,
)
from app.utils.metrics import (
    AGENT_ENERGY_LEVEL,
    AGENT_FOCUS_LEVEL,
    SIM_AGENTS_ACTIVE,
    SIM_TASKS_COMPLETED_TOTAL,
    SIM_TICKS_TOTAL,
)

logger = logging.getLogger(__name__)

# How often to sync runtime data back to agent models (ticks)
SYNC_INTERVAL = 5

# How often to attempt LLM explanation generation
LLM_EXPLANATION_INTERVAL = 15


def process_tick(state: SimulationState, rng) -> SimulationState:
    sim_id = state.sim_id
    rt = get_runtime(sim_id)

    # 1. Stat decay
    process_stat_decay(state, rng)

    # 2. Tick down ongoing conversations
    process_conversation_tick(state, rng)

    # 3. Meeting check-in (mark arrived agents as MEETING)
    process_meeting_checkin(state)

    # 4. Move MOVING agents
    for agent in state.agents.values():
        if agent.status != AgentStatus.MOVING:
            continue
        arrived = move_agent_towards_target(agent, state, rng)
        if not arrived:
            continue

        # Arrived — decide what to do
        if agent.current_task_id:
            task = state.tasks.get(agent.current_task_id)
            if task and task.status == TaskStatus.ASSIGNED and task.type != "meeting":
                # Non-meeting task: start working immediately upon arrival
                agent.status = AgentStatus.WORKING
                agent.remaining_task_ticks = task.duration_ticks
                task.status = TaskStatus.IN_PROGRESS
                task.remaining_ticks = task.duration_ticks
                add_event(
                    state,
                    "task_started",
                    {
                        "task_id": task.id,
                        "task_title": task.title,
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                    },
                )
                # Record in memory
                mem = rt.get_memory(agent.id)
                if mem:
                    mem.record_task_started(state.current_tick, task.title, task.id)
        # If no task (wanderer / break-returner): idle, maybe wander again
        elif rng.random() < 0.25:
            tx, ty = choose_wander_target(agent, rng)
            agent.target_x, agent.target_y = tx, ty
            agent.status = AgentStatus.MOVING

    # 5. Tick WORKING agents
    for agent in state.agents.values():
        if agent.status != AgentStatus.WORKING:
            continue
        if agent.remaining_task_ticks is None:
            continue
        agent.remaining_task_ticks -= 1

        if agent.remaining_task_ticks <= 0:
            task = state.tasks.get(agent.current_task_id or "")
            if task:
                task.status = TaskStatus.COMPLETED
                task.completed_tick = state.current_tick
                SIM_TASKS_COMPLETED_TOTAL.labels(sim_id=sim_id).inc()
                add_event(
                    state,
                    "task_completed",
                    {
                        "task_id": task.id,
                        "task_title": task.title,
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                    },
                )
                # Boost mood on completion
                agent.mood = min(100.0, agent.mood + 5.0)

                # Record in memory
                mem = rt.get_memory(agent.id)
                if mem:
                    mem.record_task_completed(
                        state.current_tick, task.title, task.id, task.type
                    )

            agent.current_task_id = None
            agent.remaining_task_ticks = None
            agent.status = AgentStatus.IDLE

    # 6. Tick MEETING agents (meeting task countdown handled via task)
    for task in state.tasks.values():
        if task.type != "meeting" or task.status != TaskStatus.IN_PROGRESS:
            continue
        if task.remaining_ticks is None:
            continue
        task.remaining_ticks -= 1
        if task.remaining_ticks <= 0:
            task.status = TaskStatus.COMPLETED
            task.completed_tick = state.current_tick
            SIM_TASKS_COMPLETED_TOTAL.labels(sim_id=sim_id).inc()
            # Release all agents from the meeting
            for aid in list(task.checked_in_agent_ids):
                agent = state.agents.get(aid)
                if agent:
                    agent.status = AgentStatus.IDLE
                    agent.current_task_id = None
                    agent.remaining_task_ticks = None

                    # Record in memory
                    mem = rt.get_memory(agent.id)
                    if mem:
                        other_agents = [
                            state.agents[oid].name
                            for oid in task.checked_in_agent_ids
                            if oid != aid and oid in state.agents
                        ]
                        mem.record_meeting(state.current_tick, task.title, other_agents)

            add_event(
                state,
                "meeting_ended",
                {
                    "task_id": task.id,
                    "task_title": task.title,
                    "agent_ids": list(task.checked_in_agent_ids),
                },
            )
            task.checked_in_agent_ids = []

    # 7. Check deadlines
    for task in state.tasks.values():
        if task.deadline_tick and task.deadline_tick <= state.current_tick:
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                task.status = TaskStatus.FAILED
                agent = state.agents.get(task.assigned_agent_id or "")
                if agent and agent.current_task_id == task.id:
                    agent.current_task_id = None
                    agent.remaining_task_ticks = None
                    agent.status = AgentStatus.IDLE
                    agent.mood = max(0.0, agent.mood - 10.0)

                    # Record in memory
                    mem = rt.get_memory(agent.id)
                    if mem:
                        mem.record_task_failed(
                            state.current_tick, task.title, "deadline missed"
                        )

                add_event(
                    state,
                    "task_failed",
                    {
                        "task_id": task.id,
                        "task_title": task.title,
                        "reason": "deadline missed",
                    },
                )

    # 8. Break logic
    process_break_arrival(state)
    process_breaks(state, rng)
    process_break_end(state, rng)

    # 9. Assign new tasks
    assigned_agents = assign_tasks(state, rng)

    # Record task assignments in memory
    for agent_id, task_id in assigned_agents:
        mem = rt.get_memory(agent_id)
        if mem:
            task = state.tasks.get(task_id)
            if task:
                mem.record_task_assigned(state.current_tick, task.title, task_id)

    # 10. Spontaneous conversations
    chat_pairs = process_conversations(state, rng)

    # Record conversation starts in memory
    for a1_id, a2_id in chat_pairs:
        a1 = state.agents.get(a1_id)
        a2 = state.agents.get(a2_id)
        if a1:
            mem1 = rt.get_memory(a1_id)
            if mem1 and a2:
                mem1.record_chat_started(state.current_tick, a2.name, a2_id)
        if a2:
            mem2 = rt.get_memory(a2_id)
            if mem2 and a1:
                mem2.record_chat_started(state.current_tick, a1.name, a1_id)

    # 11. Idle wandering
    for agent in state.agents.values():
        if agent.status == AgentStatus.IDLE and agent.current_task_id is None:
            if rng.random() < 0.18:
                tx, ty = choose_wander_target(agent, rng)
                agent.target_x, agent.target_y = tx, ty
                agent.status = AgentStatus.MOVING
                add_event(
                    state,
                    "agent_wandering",
                    {
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "target": {"x": tx, "y": ty},
                    },
                )

    # 12. Memory consolidation (periodic)
    for agent in state.agents.values():
        mem = rt.get_memory(agent.id)
        if mem:
            mem.maybe_consolidate(state.current_tick)

    # 13. Sync runtime → agent models (periodic, for frontend transport)
    if state.current_tick % SYNC_INTERVAL == 0:
        rt.sync_to_agents(state.agents)

    state.current_tick += 1

    # 14. Record metrics
    SIM_TICKS_TOTAL.labels(sim_id=sim_id).inc()
    SIM_AGENTS_ACTIVE.labels(sim_id=sim_id).set(len(state.agents))
    for agent in state.agents.values():
        AGENT_ENERGY_LEVEL.labels(sim_id=sim_id, agent_id=agent.id).set(agent.energy)
        AGENT_FOCUS_LEVEL.labels(sim_id=sim_id, agent_id=agent.id).set(agent.focus)

    return state
