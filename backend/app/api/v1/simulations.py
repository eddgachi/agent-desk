import random

from app.schemas import schemas
from app.simulation.core.state_manager import (
    apply_tick,
    create_simulation,
    get_simulation,
    reset_simulation,
    start_auto_loop,
    stop_auto_loop,
)
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/{sim_id}/start")
def start_simulation_auto(sim_id: str, interval: float = 0.5):
    # Check sim exists
    if not get_simulation(sim_id):
        raise HTTPException(404, "Simulation not found")
    start_auto_loop(sim_id, interval)
    return {"status": "auto loop started", "sim_id": sim_id, "interval": interval}


@router.post("/{sim_id}/stop")
def stop_simulation_auto(sim_id: str):
    stop_auto_loop(sim_id)
    return {"status": "auto loop stopped", "sim_id": sim_id}


@router.post("/", response_model=schemas.SimulationResponse)
def create_simulation_endpoint(req: schemas.CreateSimulationRequest):
    seed = req.seed if req.seed is not None else random.randint(0, 2**32 - 1)
    state = create_simulation(seed)
    return schemas.SimulationResponse(
        sim_id=state.sim_id,
        current_tick=state.current_tick,
        agents=state.agents,
        tasks=state.tasks,
        event_log=state.event_log,
    )


@router.get("/{sim_id}", response_model=schemas.SimulationResponse)
def get_simulation_endpoint(sim_id: str):
    state = get_simulation(sim_id)
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return schemas.SimulationResponse(
        sim_id=state.sim_id,
        current_tick=state.current_tick,
        agents=state.agents,
        tasks=state.tasks,
        event_log=state.event_log,
    )


@router.post("/{sim_id}/tick", response_model=schemas.TickResponse)
def tick_endpoint(sim_id: str):
    try:
        new_tick = apply_tick(sim_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return schemas.TickResponse(sim_id=sim_id, new_tick=new_tick)


@router.post("/{sim_id}/reset", response_model=schemas.SimulationResponse)
def reset_endpoint(sim_id: str):
    state = reset_simulation(sim_id)
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return schemas.SimulationResponse(
        sim_id=state.sim_id,
        current_tick=state.current_tick,
        agents=state.agents,
        tasks=state.tasks,
        event_log=state.event_log,
    )
