import random

from app.config import settings
from app.schemas import schemas
from app.simulation.core.runtime_manager import get_runtime
from app.simulation.core.serializers import (
    serialize_agent,
    serialize_event,
    serialize_state,
)
from app.simulation.core.state_manager import (
    apply_tick,
    create_simulation,
    get_simulation,
    reset_simulation,
    start_auto_loop,
    stop_auto_loop,
)
from app.simulation.core.ws_manager import ws_manager
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/simulations", tags=["simulations"])


# ── REST: simulation lifecycle ─────────────────────────────


@router.post("/", response_model=schemas.SimulationResponse)
def create_simulation_endpoint(req: schemas.CreateSimulationRequest):
    seed = req.seed if req.seed is not None else random.randint(0, 2**32 - 1)
    state = create_simulation(seed)
    return _state_to_response(state)


@router.get("/{sim_id}", response_model=schemas.SimulationResponse)
def get_simulation_endpoint(sim_id: str):
    state = get_simulation(sim_id)
    if not state:
        raise HTTPException(404, "Simulation not found")
    return _state_to_response(state)


@router.post("/{sim_id}/tick", response_model=schemas.TickResponse)
async def tick_endpoint(sim_id: str):
    if not get_simulation(sim_id):
        raise HTTPException(404, "Simulation not found")
    try:
        new_tick = await apply_tick(sim_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return schemas.TickResponse(sim_id=sim_id, new_tick=new_tick)


@router.post("/{sim_id}/reset", response_model=schemas.SimulationResponse)
async def reset_endpoint(sim_id: str):
    state = reset_simulation(sim_id)
    if not state:
        raise HTTPException(404, "Simulation not found")
    await ws_manager.broadcast_snapshot(sim_id, serialize_state(state))
    return _state_to_response(state)


@router.post("/{sim_id}/start")
async def start_simulation_auto(sim_id: str, interval: float = 1.0):
    if not get_simulation(sim_id):
        raise HTTPException(404, "Simulation not found")
    start_auto_loop(sim_id, interval)
    return {"status": "started", "sim_id": sim_id, "interval": interval}


@router.post("/{sim_id}/stop")
async def stop_simulation_auto(sim_id: str):
    if not get_simulation(sim_id):
        raise HTTPException(404, "Simulation not found")
    stop_auto_loop(sim_id)
    return {"status": "stopped", "sim_id": sim_id}


# ── Phase 7: Memory endpoints ──────────────────────────────


@router.get("/{sim_id}/agents/{agent_id}/memory")
def get_agent_memory(sim_id: str, agent_id: str):
    """Get detailed structured memory for a specific agent."""
    state = get_simulation(sim_id)
    if not state:
        raise HTTPException(404, "Simulation not found")
    if agent_id not in state.agents:
        raise HTTPException(404, "Agent not found")

    rt = get_runtime(sim_id)
    mem = rt.get_memory(agent_id)
    dec = rt.get_decisions(agent_id)

    return {
        "agent_id": agent_id,
        "agent_name": state.agents[agent_id].name,
        "memory": {
            "working": mem.working.to_dict_list() if mem else [],
            "episodic": mem.episodic.to_dict_list() if mem else [],
            "semantic": mem.semantic.to_dict() if mem else {},
            "last_consolidation": mem._last_consolidation_tick if mem else 0,
        },
        "decision_engine": dec.to_dict() if dec else {},
        "serialized_agent": serialize_agent(state.agents[agent_id]),
    }


# ── Phase 8/9: LLM configuration ─────────────────────────


@router.post("/{sim_id}/llm/enable")
async def enable_llm(sim_id: str):
    """Enable LLM-enhanced decisions for this simulation."""
    if not settings.DEEPSEEK_API_KEY:
        raise HTTPException(400, "DEEPSEEK_API_KEY not configured on server")

    state = get_simulation(sim_id)
    if not state:
        raise HTTPException(404, "Simulation not found")

    rt = get_runtime(sim_id)
    if not rt.llm_client:
        rt.setup_llm()

    # Enable LLM on all agents' decision engines
    for agent_id in state.agents:
        dec = rt.get_decisions(agent_id)
        if dec and rt.llm_client:
            dec.enable_llm(rt.llm_client)

    return {
        "status": "llm_enabled",
        "sim_id": sim_id,
        "agent_count": len(state.agents),
    }


@router.post("/{sim_id}/llm/disable")
async def disable_llm(sim_id: str):
    """Disable LLM-enhanced decisions for this simulation."""
    state = get_simulation(sim_id)
    if not state:
        raise HTTPException(404, "Simulation not found")

    rt = get_runtime(sim_id)
    for agent_id in state.agents:
        dec = rt.get_decisions(agent_id)
        if dec:
            dec.disable_llm()

    return {
        "status": "llm_disabled",
        "sim_id": sim_id,
    }


@router.get("/{sim_id}/llm/status")
def get_llm_status(sim_id: str):
    """Get LLM usage status for this simulation."""
    state = get_simulation(sim_id)
    if not state:
        raise HTTPException(404, "Simulation not found")

    from app.simulation.llm.rate_limiter import rate_limiter

    budget = rate_limiter.get_budget(sim_id)
    rt = get_runtime(sim_id)

    agents_status = {}
    for agent_id in state.agents:
        dec = rt.get_decisions(agent_id)
        agents_status[agent_id] = {
            "use_llm": dec.use_llm if dec else False,
            "budget": dec.to_dict().get("budget", {}) if dec else {},
        }

    return {
        "sim_id": sim_id,
        "global_enabled": settings.LLM_ENABLED,
        "api_key_configured": bool(settings.DEEPSEEK_API_KEY),
        "global_budget": budget.to_dict(),
        "agents": agents_status,
    }


# ── WebSocket ──────────────────────────────────────────────


@router.websocket("/{sim_id}/ws")
async def simulation_ws(websocket: WebSocket, sim_id: str):
    state = get_simulation(sim_id)
    if not state:
        await websocket.close(code=4004)
        return

    await ws_manager.connect(sim_id, websocket)

    # Send full state snapshot immediately on connect
    snapshot = serialize_state(state)
    snapshot["event_log"] = [serialize_event(e) for e in state.event_log[-100:]]
    await websocket.send_json({"type": "state_snapshot", "data": snapshot})

    try:
        while True:
            msg = await websocket.receive_json()
            await _handle_client_message(sim_id, msg, websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(sim_id, websocket)
    except Exception:
        ws_manager.disconnect(sim_id, websocket)


async def _handle_client_message(sim_id: str, msg: dict, ws: WebSocket) -> None:
    """Process commands sent from the frontend over the WebSocket."""
    cmd = msg.get("cmd")
    if cmd == "ping":
        await ws.send_json({"type": "pong"})
    elif cmd == "tick":
        await apply_tick(sim_id)
    elif cmd == "start":
        interval = float(msg.get("interval", 1.0))
        start_auto_loop(sim_id, interval)
        await ws.send_json({"type": "ack", "cmd": "start"})
    elif cmd == "stop":
        stop_auto_loop(sim_id)
        await ws.send_json({"type": "ack", "cmd": "stop"})


# ── Helper ─────────────────────────────────────────────────


def _state_to_response(state) -> schemas.SimulationResponse:
    from app.simulation.core.runtime_manager import get_runtime

    # Sync runtime data before serializing
    rt = get_runtime(state.sim_id)
    rt.sync_to_agents(state.agents)

    return schemas.SimulationResponse(
        sim_id=state.sim_id,
        current_tick=state.current_tick,
        running=state.running,
        agents={aid: a.model_dump() for aid, a in state.agents.items()},
        tasks={tid: t.model_dump() for tid, t in state.tasks.items()},
        event_log=[e.model_dump() for e in state.event_log[-50:]],
    )
