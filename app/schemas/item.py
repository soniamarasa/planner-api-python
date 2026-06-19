from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.item import Item
from app.services.week_utils import is_item_overdue


class ItemBase(BaseModel):
    description: str
    type: str | None = None
    where: str | list[str] | None = None
    obs: str | None = None
    estimated_pomodoros: float | None = Field(default=1.0, ge=0.1, le=100)
    week_start: date | None = None
    scheduled_date: date | None = None
    project_id: UUID | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    estimated_pomodoros: float | None = Field(default=None, ge=0.1, le=100)


class ItemReschedule(BaseModel):
    scheduled_date: date
    where: str | None = None


class ItemStatusUpdate(BaseModel):
    started: bool | None = None
    finished: bool | None = None
    important: bool | None = None
    canceled: bool | None = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    description: str
    type: str | None
    where: str | None
    scheduled_date: date | None
    carried_from: date | None
    obs: str | None
    started: bool
    finished: bool
    important: bool
    canceled: bool
    focus_seconds_total: int
    estimated_pomodoros: float
    pomodoros_completed: float = 0.0
    task_focus_progress: float = 0.0
    is_overdue: bool = False
    project_id: UUID | None = None
    project_name: str | None = None
    project_icon: str | None = None
    project_color: str | None = None


def build_item_response(item: Item, work_minutes: int = 25, today: date | None = None) -> ItemResponse:
    pomodoro_seconds = work_minutes * 60
    pomodoros_completed = round(item.focus_seconds_total / pomodoro_seconds, 4) if pomodoro_seconds else 0.0
    target_seconds = item.estimated_pomodoros * pomodoro_seconds
    task_focus_progress = (
        round(min(item.focus_seconds_total / target_seconds, 1.0), 4) if target_seconds else 0.0
    )

    return ItemResponse(
        id=item.id,
        user_id=item.user_id,
        description=item.description,
        type=item.type,
        where=item.where,
        scheduled_date=item.scheduled_date,
        carried_from=item.carried_from,
        obs=item.obs,
        started=item.started,
        finished=item.finished,
        important=item.important,
        canceled=item.canceled,
        focus_seconds_total=item.focus_seconds_total,
        estimated_pomodoros=item.estimated_pomodoros,
        pomodoros_completed=pomodoros_completed,
        task_focus_progress=task_focus_progress,
        is_overdue=is_item_overdue(
            item.scheduled_date,
            item.finished,
            item.canceled,
            item.type,
            item.where,
            today,
        ),
        project_id=item.project_id,
        project_name=item.project.name if item.project else None,
        project_icon=item.project.icon if item.project else None,
        project_color=item.project.color if item.project else None,
    )


class MessageResponse(BaseModel):
    message: str
