from app.simulation.core.event_logger import add_event
from app.simulation.models.simulation_state import (
    AgentStatus,
    SimulationState,
    TaskStatus,
)


def assign_tasks(state: SimulationState, rng):
    # Get pending tasks sorted by priority (higher first), then by deadline (earlier first)
    pending_tasks = [t for t in state.tasks.values() if t.status == TaskStatus.PENDING]
    pending_tasks.sort(
        key=lambda t: (-t.priority, t.deadline_tick if t.deadline_tick else 999999)
    )

    # Eligible agents: idle or moving? We'll consider idle only for simplicity
    eligible_agents = [a for a in state.agents.values() if a.status == AgentStatus.IDLE]

    for task in pending_tasks:
        # Find best eligible agent
        best_agent = None
        best_distance = float("inf")
        for agent in eligible_agents:
            # Check role requirement
            if task.required_role and agent.role != task.required_role:
                continue
            # For location requirement, agent must be able to move there; we can assign anyway and agent will move
            # Calculate distance from current position to task location (if any)
            if task.required_location:
                lx, ly = task.required_location
                dist = abs(agent.position_x - lx) + abs(
                    agent.position_y - ly
                )  # Manhattan
            else:
                dist = 0
            if dist < best_distance:
                best_distance = dist
                best_agent = agent

        if best_agent:
            # Assign task
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent_id = best_agent.id
            best_agent.current_task_id = task.id
            # If task has location and agent not already there, set moving target
            if task.required_location:
                best_agent.target_x, best_agent.target_y = task.required_location
                best_agent.status = AgentStatus.MOVING
                add_event(
                    state,
                    "agent_started_moving",
                    {
                        "agent_id": best_agent.id,
                        "target": [best_agent.target_x, best_agent.target_y],
                        "reason": f"move to task {task.id}",
                    },
                )
            else:
                # Start task immediately
                best_agent.status = AgentStatus.WORKING
                best_agent.remaining_task_ticks = task.duration_ticks
                task.status = TaskStatus.IN_PROGRESS
                add_event(
                    state,
                    "task_started",
                    {
                        "task_id": task.id,
                        "agent_id": best_agent.id,
                        "tick": state.current_tick,
                    },
                )
            add_event(
                state, "task_assigned", {"task_id": task.id, "agent_id": best_agent.id}
            )
            # Remove agent from eligible list (only one task per agent for now)
            eligible_agents.remove(best_agent)
    return state
