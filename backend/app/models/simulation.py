import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DBAgentStatus(enum.Enum):
    idle = "idle"
    working = "working"
    meeting = "meeting"
    break_ = "break"
    moving = "moving"


class DBTaskStatus(enum.Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class SimulationModel(Base):
    __tablename__ = "simulations"
    id = Column(String, primary_key=True)
    seed = Column(Integer, nullable=False)
    current_tick = Column(Integer, default=0)
    created_at = Column(DateTime)


class AgentModel(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    simulation_id = Column(String, index=True)
    name = Column(String)
    role = Column(String)
    position_x = Column(Float)
    position_y = Column(Float)
    status = Column(Enum(DBAgentStatus))
    energy = Column(Integer)
    focus = Column(Integer)


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    simulation_id = Column(String, index=True)
    title = Column(String)
    description = Column(String)
    type = Column(String)
    duration_ticks = Column(Integer)
    required_location = Column(JSON, nullable=True)  # store as [x,y]
    required_role = Column(String, nullable=True)
    priority = Column(Integer)
    deadline_tick = Column(Integer, nullable=True)
    assigned_agent_id = Column(String, nullable=True)
    status = Column(Enum(DBTaskStatus))


class EventModel(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    simulation_id = Column(String, index=True)
    tick = Column(Integer)
    type = Column(String)
    payload = Column(JSON)
    source = Column(String)
