from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    icon: str = Field(default="pi-briefcase", max_length=80)
    color: str = Field(default="#ff9a3d", max_length=20)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    icon: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=20)
    archived: bool | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    icon: str
    color: str
    archived: bool
    open_tasks_count: int = 0
    focus_seconds_total: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    icon: str
    color: str


class UnassignedSummary(BaseModel):
    open_count: int = 0
