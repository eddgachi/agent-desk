from app.simulation.core.event_logger import add_event
from app.simulation.core.movement import (
    choose_random_wander_target,
    move_agent_towards_target,
)
from app.simulation.core.task_assignment import assign_tasks
from app.simulation.models.simulation_state import (
    AgentStatus,
    SimulationState,
    TaskStatus,
)


def process_tick(state: SimulationState, rng):
    # 1. Process movement for agents that are moving
    for agent in state.agents.values():
        if agent.status == AgentStatus.MOVING:
            arrived = move_agent_towards_target(agent, state, rng)
            if arrived:
                # If agent has a task associated and arrived at target, start working
                if agent.current_task_id:
                    task = state.tasks.get(agent.current_task_id)
                    if task and task.status == TaskStatus.ASSIGNED:
                        agent.status = AgentStatus.WORKING
                        agent.remaining_task_ticks = task.duration_ticks
                        task.status = TaskStatus.IN_PROGRESS
                        add_event(
                            state,
                            "task_started",
                            {
                                "task_id": task.id,
                                "agent_id": agent.id,
                                "tick": state.current_tick,
                            },
                        )
                else:
                    # Idle wanderer arrived, choose new wander target
                    if rng.random() < 0.3:  # chance to wander again
                        nx, ny = choose_random_wander_target(agent, rng)
                        agent.target_x, agent.target_y = nx, ny
                        agent.status = AgentStatus.MOVING
                        add_event(
                            state,
                            "agent_started_moving",
                            {
                                "agent_id": agent.id,
                                "target": [nx, ny],
                                "reason": "wandering",
                            },
                        )

    # 2. Process working agents: decrement task ticks and complete if done
    for agent in state.agents.values():
        if (
            agent.status == AgentStatus.WORKING
            and agent.remaining_task_ticks is not None
        ):
            agent.remaining_task_ticks -= 1
            if agent.remaining_task_ticks <= 0:
                # Task completed
                task = state.tasks.get(agent.current_task_id)
                if task:
                    task.status = TaskStatus.COMPLETED
                    add_event(
                        state,
                        "task_completed",
                        {
                            "task_id": task.id,
                            "agent_id": agent.id,
                            "tick": state.current_tick,
                        },
                    )
                agent.current_task_id = None
                agent.remaining_task_ticks = None
                agent.status = AgentStatus.IDLE
                # After completing task, maybe start wandering?
                if rng.random() < 0.5:
                    nx, ny = choose_random_wander_target(agent, rng)
                    agent.target_x, agent.target_y = nx, ny
                    agent.status = AgentStatus.MOVING
                    add_event(
                        state,
                        "agent_started_moving",
                        {
                            "agent_id": agent.id,
                            "target": [nx, ny],
                            "reason": "post-task wandering",
                        },
                    )

    # 3. Check task deadlines (fail if passed)
    for task in state.tasks.values():
        if task.deadline_tick and task.deadline_tick <= state.current_tick:
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                task.status = TaskStatus.FAILED
                if task.assigned_agent_id:
                    agent = state.agents.get(task.assigned_agent_id)
                    if agent and agent.current_task_id == task.id:
                        agent.current_task_id = None
                        agent.remaining_task_ticks = None
                        agent.status = AgentStatus.IDLE
                add_event(
                    state,
                    "task_failed",
                    {
                        "task_id": task.id,
                        "reason": "deadline missed",
                        "tick": state.current_tick,
                    },
                )

    # 4. Assign new tasks to idle agents (including newly idle from completion)
    assign_tasks(state, rng)

    # 5. For idle agents with no task, maybe wander
    for agent in state.agents.values():
        if agent.status == AgentStatus.IDLE and agent.current_task_id is None:
            if rng.random() < 0.2:  # 20% chance per tick to start wandering
                nx, ny = choose_random_wander_target(agent, rng)
                agent.target_x, agent.target_y = nx, ny
                agent.status = AgentStatus.MOVING
                add_event(
                    state,
                    "agent_started_moving",
                    {
                        "agent_id": agent.id,
                        "target": [nx, ny],
                        "reason": "idle wandering",
                    },
                )

    # Increment tick
    state.current_tick += 1
    return state
