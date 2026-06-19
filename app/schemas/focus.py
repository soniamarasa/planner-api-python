from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FocusSettingsUpdate(BaseModel):
    work_minutes: int | None = Field(default=None, ge=1, le=180)
    short_break_minutes: int | None = Field(default=None, ge=1, le=60)
    long_break_minutes: int | None = Field(default=None, ge=1, le=60)
    long_break_interval: int | None = Field(default=None, ge=1, le=20)
    ambient_sound: str | None = Field(default=None, max_length=50)
    sound_volume: float | None = Field(default=None, ge=0.0, le=1.0)
    background_id: str | None = Field(default=None, max_length=50)
    auto_start_breaks: bool | None = None
    auto_start_focus: bool | None = None
    notify_on_complete: bool | None = None


class FocusSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    work_minutes: int
    short_break_minutes: int
    long_break_minutes: int
    long_break_interval: int
    ambient_sound: str
    sound_volume: float
    background_id: str
    auto_start_breaks: bool
    auto_start_focus: bool
    notify_on_complete: bool


class PomodoroSessionStart(BaseModel):
    item_id: UUID


class PomodoroSessionSync(BaseModel):
    elapsed_seconds: int = Field(ge=0)


class PomodoroSessionAbandon(BaseModel):
    elapsed_seconds: int = Field(default=0, ge=0)
    credit_partial: bool = True


class PomodoroSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    item_id: UUID
    status: str
    target_seconds: int
    elapsed_seconds: int
    credited_seconds: int
    started_at: str
    paused_at: str | None
    ended_at: str | None
    cycle_progress: float
    item_focus_seconds_total: int
    item_estimated_pomodoros: float
    item_pomodoros_completed: float


class PomodoroSessionListResponse(BaseModel):
    sessions: list[PomodoroSessionResponse]
