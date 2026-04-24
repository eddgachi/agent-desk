from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CreateSimulationRequest(BaseModel):
    seed: Optional[int] = None


class SimulationResponse(BaseModel):
    sim_id:       str
    current_tick: int
    running:      bool = False
    # Plain dicts — avoids re-serialising Pydantic models twice
    agents:    Dict[str, Any]
    tasks:     Dict[str, Any]
    event_log: List[Any]


class TickResponse(BaseModel):
    sim_id:   str
    new_tick: int
