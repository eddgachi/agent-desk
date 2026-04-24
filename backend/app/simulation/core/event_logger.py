import uuid

from app.simulation.models.simulation_state import Event, SimulationState


def add_event(
    state: SimulationState, event_type: str, payload: dict, source: str = "engine"
):
    event = Event(
        event_id=str(uuid.uuid4()),
        tick=state.current_tick,
        type=event_type,
        payload=payload,
        source=source,
    )
    state.event_log.append(event)
    # In Phase 2 we don't persist to DB yet
