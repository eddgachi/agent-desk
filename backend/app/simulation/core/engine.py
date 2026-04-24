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
  11. Increment tick counter
"""
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
from app.simulation.core.movement import (
    choose_wander_target,
    move_agent_towards_target,
)
from app.simulation.core.task_assignment import assign_tasks
from app.simulation.models.simulation_state import (
    AgentStatus,
    SimulationState,
    TaskStatus,
)


def process_tick(state: SimulationState, rng) -> SimulationState:
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
                add_event(state, "task_started", {
                    "task_id":    task.id,
                    "task_title": task.title,
                    "agent_id":   agent.id,
                    "agent_name": agent.name,
                })
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
                task.status       = TaskStatus.COMPLETED
                task.completed_tick = state.current_tick
                add_event(state, "task_completed", {
                    "task_id":    task.id,
                    "task_title": task.title,
                    "agent_id":   agent.id,
                    "agent_name": agent.name,
                })
                # Boost mood on completion
                agent.mood = min(100.0, agent.mood + 5.0)
                agent.memory.append(f"Tick {state.current_tick}: completed '{task.title}'")
                if len(agent.memory) > 20:
                    agent.memory = agent.memory[-20:]

            agent.current_task_id      = None
            agent.remaining_task_ticks = None
            agent.status               = AgentStatus.IDLE

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
            # Release all agents from the meeting
            for aid in list(task.checked_in_agent_ids):
                agent = state.agents.get(aid)
                if agent:
                    agent.status              = AgentStatus.IDLE
                    agent.current_task_id     = None
                    agent.remaining_task_ticks = None
                    agent.memory.append(f"Tick {state.current_tick}: attended '{task.title}'")
            add_event(state, "meeting_ended", {
                "task_id":    task.id,
                "task_title": task.title,
                "agent_ids":  list(task.checked_in_agent_ids),
                "agent_name": ", ".join(
                    state.agents[aid].name
                    for aid in task.checked_in_agent_ids
                    if aid in state.agents
                ),
            })
            task.checked_in_agent_ids = []

    # 7. Check deadlines
    for task in state.tasks.values():
        if task.deadline_tick and task.deadline_tick <= state.current_tick:
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                task.status = TaskStatus.FAILED
                agent = state.agents.get(task.assigned_agent_id or "")
                if agent and agent.current_task_id == task.id:
                    agent.current_task_id      = None
                    agent.remaining_task_ticks = None
                    agent.status               = AgentStatus.IDLE
                    agent.mood = max(0.0, agent.mood - 10.0)
                add_event(state, "task_failed", {
                    "task_id":    task.id,
                    "task_title": task.title,
                    "reason":     "deadline missed",
                })

    # 8. Break logic
    process_break_arrival(state)
    process_breaks(state, rng)
    process_break_end(state, rng)

    # 9. Assign new tasks
    assign_tasks(state, rng)

    # 10. Spontaneous conversations
    process_conversations(state, rng)

    # 11. Idle wandering
    for agent in state.agents.values():
        if agent.status == AgentStatus.IDLE and agent.current_task_id is None:
            if rng.random() < 0.18:
                tx, ty = choose_wander_target(agent, rng)
                agent.target_x, agent.target_y = tx, ty
                agent.status = AgentStatus.MOVING
                add_event(state, "agent_wandering", {
                    "agent_id":   agent.id,
                    "agent_name": agent.name,
                    "target":     {"x": tx, "y": ty},
                })

    state.current_tick += 1
    return state
