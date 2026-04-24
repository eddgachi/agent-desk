import math

from app.simulation.core.event_logger import add_event
from app.simulation.models.simulation_state import (
    AgentStatus,
    SimulationState,
    TaskStatus,
)


def assign_tasks(state: SimulationState, rng) -> SimulationState:
    """
    Greedy task assignment:
      - Sort pending tasks by priority (desc) then deadline (asc).
      - For each task, find the best eligible idle agent.
      - Agents with very low focus or energy are not assigned new work tasks.
    """
    pending = [t for t in state.tasks.values() if t.status == TaskStatus.PENDING]
    pending.sort(key=lambda t: (-t.priority, t.deadline_tick or 999_999))

    eligible = [
        a for a in state.agents.values()
        if a.status == AgentStatus.IDLE and a.current_task_id is None
    ]

    for task in pending:
        best_agent = None
        best_score = float("inf")

        for agent in eligible:
            # Role check
            if task.required_role and agent.role != task.required_role:
                continue
            # Don't assign heavy work to exhausted agents
            if task.type in ("work", "research", "review") and agent.energy < 25:
                continue

            # Score = distance to task location (0 if no location required)
            if task.required_location:
                lx, ly = task.required_location
                dist = math.hypot(agent.position_x - lx, agent.position_y - ly)
            else:
                dist = 0.0

            # Prefer agents with higher focus for cognitively demanding tasks
            focus_penalty = max(0.0, (100 - agent.focus) * 0.1)
            score = dist + focus_penalty

            if score < best_score:
                best_score = score
                best_agent = agent

        if best_agent is None:
            continue

        # Assign
        task.status           = TaskStatus.ASSIGNED
        task.assigned_agent_id = best_agent.id
        if best_agent.id not in task.assigned_agents:
            task.assigned_agents.append(best_agent.id)
        best_agent.current_task_id = task.id

        if task.required_location:
            lx, ly = task.required_location
            best_agent.target_x = float(lx)
            best_agent.target_y = float(ly)
            best_agent.status   = AgentStatus.MOVING
        else:
            best_agent.status              = AgentStatus.WORKING
            best_agent.remaining_task_ticks = task.duration_ticks
            task.status                    = TaskStatus.IN_PROGRESS
            task.remaining_ticks           = task.duration_ticks
            add_event(state, "task_started", {
                "task_id":    task.id,
                "task_title": task.title,
                "agent_id":   best_agent.id,
                "agent_name": best_agent.name,
            })

        add_event(state, "task_assigned", {
            "task_id":    task.id,
            "task_title": task.title,
            "agent_id":   best_agent.id,
            "agent_name": best_agent.name,
        })

        eligible.remove(best_agent)

    return state
