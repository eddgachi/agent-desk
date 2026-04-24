from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    MEETING = "meeting"
    BREAK = "break"
    MOVING = "moving"


class Agent(BaseModel):
    id: str
    name: str
    role: str
    position_x: float
    position_y: float
    status: AgentStatus
    current_task_id: Optional[str] = None
    energy: int = 100  # 0-100
    focus: int = 100  # 0-100
    assigned_tasks: List[str] = []  # task ids


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    id: str
    title: str
    description: str
    type: str  # "work", "meeting", "break"
    duration_ticks: int
    required_location: Optional[tuple[float, float]] = None  # (x,y)
    required_role: Optional[str] = None
    priority: int = 0  # higher = more important
    deadline_tick: Optional[int] = None
    assigned_agent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    remaining_ticks: Optional[int] = None


class Event(BaseModel):
    event_id: str
    tick: int
    type: str
    payload: dict
    source: str  # "engine" or "agent"


class SimulationState(BaseModel):
    sim_id: str
    current_tick: int = 0
    agents: Dict[str, Agent] = Field(default_factory=dict)
    tasks: Dict[str, Task] = Field(default_factory=dict)
    event_log: List[Event] = Field(default_factory=list)
    seed: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
