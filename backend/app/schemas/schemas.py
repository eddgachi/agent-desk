from typing import Dict, List, Optional

from app.simulation.models.simulation_state import Agent, Event, Task
from pydantic import BaseModel


class CreateSimulationRequest(BaseModel):
    seed: Optional[int] = None  # if None, generate random


class SimulationResponse(BaseModel):
    sim_id: str
    current_tick: int
    agents: Dict[str, Agent]
    tasks: Dict[str, Task]
    event_log: List[Event]


class TickResponse(BaseModel):
    sim_id: str
    new_tick: int
