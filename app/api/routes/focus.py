from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.focus import (
    FocusSettingsResponse,
    FocusSettingsUpdate,
    PomodoroSessionAbandon,
    PomodoroSessionListResponse,
    PomodoroSessionResponse,
    PomodoroSessionStart,
    PomodoroSessionSync,
)
from app.services import focus_service

router = APIRouter()


@router.get("/focus/settings/{user_id}", response_model=FocusSettingsResponse)
def get_focus_settings(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> FocusSettingsResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.get_or_create_settings(db, user_id)


@router.put("/focus/settings/{user_id}", response_model=FocusSettingsResponse)
def update_focus_settings(
    user_id: UUID,
    payload: FocusSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> FocusSettingsResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.update_settings(db, user_id, payload)


@router.get("/focus/sessions/{user_id}/active", response_model=PomodoroSessionResponse | None)
def get_active_pomodoro_session(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse | None:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.get_active_session_response(db, user_id)


@router.get("/focus/sessions/{user_id}", response_model=PomodoroSessionListResponse)
def list_pomodoro_sessions(
    user_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionListResponse:
    focus_service.assert_user_access(current_user, user_id)
    sessions = focus_service.list_sessions(db, user_id, limit)
    return PomodoroSessionListResponse(sessions=sessions)


@router.post("/focus/sessions/{user_id}", response_model=PomodoroSessionResponse)
def start_pomodoro_session(
    user_id: UUID,
    payload: PomodoroSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.start_session(db, user_id, payload.item_id)


@router.put("/focus/sessions/{user_id}/{session_id}/pause", response_model=PomodoroSessionResponse)
def pause_pomodoro_session(
    user_id: UUID,
    session_id: UUID,
    payload: PomodoroSessionSync,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.pause_session(db, user_id, session_id, payload.elapsed_seconds)


@router.put("/focus/sessions/{user_id}/{session_id}/resume", response_model=PomodoroSessionResponse)
def resume_pomodoro_session(
    user_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.resume_session(db, user_id, session_id)


@router.put("/focus/sessions/{user_id}/{session_id}/sync", response_model=PomodoroSessionResponse)
def sync_pomodoro_session(
    user_id: UUID,
    session_id: UUID,
    payload: PomodoroSessionSync,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.sync_session(db, user_id, session_id, payload.elapsed_seconds)


@router.put("/focus/sessions/{user_id}/{session_id}/complete", response_model=PomodoroSessionResponse)
def complete_pomodoro_session(
    user_id: UUID,
    session_id: UUID,
    payload: PomodoroSessionSync,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.complete_session(db, user_id, session_id, payload.elapsed_seconds)


@router.put("/focus/sessions/{user_id}/{session_id}/abandon", response_model=PomodoroSessionResponse)
def abandon_pomodoro_session(
    user_id: UUID,
    session_id: UUID,
    payload: PomodoroSessionAbandon,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PomodoroSessionResponse:
    focus_service.assert_user_access(current_user, user_id)
    return focus_service.abandon_session(
        db,
        user_id,
        session_id,
        payload.elapsed_seconds,
        payload.credit_partial,
    )
