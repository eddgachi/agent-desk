"""
Serialization helpers: convert simulation state objects → plain dicts
suitable for JSON responses and WebSocket messages.
"""

from app.simulation.models.simulation_state import Agent, Event, SimulationState, Task


def serialize_agent(agent: Agent) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "position_x": round(agent.position_x, 2),
        "position_y": round(agent.position_y, 2),
        "target_x": round(agent.target_x, 2) if agent.target_x is not None else None,
        "target_y": round(agent.target_y, 2) if agent.target_y is not None else None,
        "status": agent.status.value,
        "energy": round(agent.energy, 1),
        "focus": round(agent.focus, 1),
        "mood": round(agent.mood, 1),
        "current_task_id": agent.current_task_id,
        "remaining_task_ticks": agent.remaining_task_ticks,
        "desk_id": agent.desk_id,
        "conversation_partner_id": agent.conversation_partner_id,
        "memory": agent.memory[-10:],
        # ── Phase 7: Structured memory ──
        "working_memory": agent.working_memory[-20:] if agent.working_memory else [],
        "episodic_memory": agent.episodic_memory[-30:] if agent.episodic_memory else [],
        "semantic_memory": agent.semantic_memory or {},
        "memory_last_consolidation": agent.memory_last_consolidation,
        # ── Phase 8/9: LLM explanations ──
        "llm_explanation": agent.llm_explanation,
        "llm_feeling": agent.llm_feeling,
        "llm_next_plan": agent.llm_next_plan,
        "is_thinking": agent.is_thinking,
    }


def serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "type": task.type,
        "status": task.status.value,
        "duration_ticks": task.duration_ticks,
        "remaining_ticks": task.remaining_ticks,
        "required_role": task.required_role,
        "required_location": task.required_location,
        "priority": task.priority,
        "deadline_tick": task.deadline_tick,
        "assigned_agent_id": task.assigned_agent_id,
        "assigned_agents": task.assigned_agents,
        "completed_tick": task.completed_tick,
    }


def serialize_event(event: Event) -> dict:
    return {
        "event_id": event.event_id,
        "tick": event.tick,
        "type": event.type,
        "payload": event.payload,
        "source": event.source,
    }


def serialize_state(state: SimulationState) -> dict:
    """Full state snapshot — used on WS connect and for state_snapshot messages."""
    return {
        "sim_id": state.sim_id,
        "current_tick": state.current_tick,
        "running": state.running,
        "agents": {aid: serialize_agent(a) for aid, a in state.agents.items()},
        "tasks": {tid: serialize_task(t) for tid, t in state.tasks.items()},
        "event_log": [serialize_event(e) for e in state.event_log[-50:]],
    }


def serialize_tick_update(state: SimulationState) -> dict:
    """Lightweight tick update — agents + tasks + tick number, no event log."""
    return {
        "current_tick": state.current_tick,
        "running": state.running,
        "agents": {aid: serialize_agent(a) for aid, a in state.agents.items()},
        "tasks": {tid: serialize_task(t) for tid, t in state.tasks.items()},
    }
