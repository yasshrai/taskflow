from pydantic import BaseModel, ConfigDict
from enum import Enum


class TaskStatusCode(Enum):
    PENDING = "pending"
    CANCELED = "canceled"
    COMPLETED = "completed"
    CREATED = "created"


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None = None
    assigned_to: list[str]
    assigned_by: str
    status: str


class TaskUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    title: str
    description: str | None = None
    status: str


class TaskCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None = None
    status: TaskStatusCode
    assigned_to: list[str]


class TaskStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    newStatus: TaskStatusCode
