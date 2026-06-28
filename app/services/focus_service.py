from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.focus_settings import FocusSettings
from app.models.item import Item
from app.models.pomodoro_session import PomodoroSession
from app.models.user import User
from app.schemas.focus import FocusSettingsUpdate, PomodoroSessionResponse

ACTIVE_STATUSES = ("running", "paused")
TERMINAL_STATUSES = ("completed", "abandoned")


def assert_user_access(current_user: User, user_id: UUID) -> None:
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )


def get_or_create_settings(db: Session, user_id: UUID) -> FocusSettings:
    settings = db.scalar(select(FocusSettings).where(FocusSettings.user_id == user_id))
    if settings:
        return settings

    settings = FocusSettings(user_id=user_id)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_settings(db: Session, user_id: UUID, payload: FocusSettingsUpdate) -> FocusSettings:
    settings = get_or_create_settings(db, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def abandon_active_sessions_for_item(db: Session, user_id: UUID, item_id: UUID) -> None:
    """Closes any running/paused session tied to an item. Called when a task is
    finished or canceled so it doesn't leave a dangling, unresolvable session."""
    sessions = db.scalars(
        select(PomodoroSession).where(
            PomodoroSession.user_id == user_id,
            PomodoroSession.item_id == item_id,
            PomodoroSession.status.in_(ACTIVE_STATUSES),
        )
    ).all()
    now = datetime.now(UTC)
    for session in sessions:
        session.status = "abandoned"
        session.ended_at = now
        session.paused_at = None
        db.add(session)


def get_active_session(db: Session, user_id: UUID) -> PomodoroSession | None:
    return db.scalar(
        select(PomodoroSession)
        .where(
            PomodoroSession.user_id == user_id,
            PomodoroSession.status.in_(ACTIVE_STATUSES),
        )
        .order_by(PomodoroSession.started_at.desc())
    )


def get_session_for_user(db: Session, user_id: UUID, session_id: UUID) -> PomodoroSession:
    session = db.get(PomodoroSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pomodoro session not found.")
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this session.")
    return session


def get_owned_item(db: Session, user_id: UUID, item_id: UUID) -> Item:
    """Fetches an item enforcing only ownership. Used for transitions on an
    existing session, which must keep working even if the task was later
    finished or canceled."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this item.")
    return item


def get_task_item(db: Session, user_id: UUID, item_id: UUID) -> Item:
    """Fetches an item enforcing the rules required to START a pomodoro."""
    item = get_owned_item(db, user_id, item_id)
    if item.type != "task":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pomodoro is only available for tasks.")
    if item.finished or item.canceled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot start pomodoro on a finished or canceled task.")
    return item


def credit_focus_time(session: PomodoroSession, item: Item, elapsed_seconds: int) -> None:
    elapsed_seconds = max(0, min(elapsed_seconds, session.target_seconds))
    session.elapsed_seconds = elapsed_seconds
    delta = elapsed_seconds - session.credited_seconds
    if delta > 0:
        item.focus_seconds_total += delta
        session.credited_seconds = elapsed_seconds


def build_session_response(session: PomodoroSession, item: Item) -> PomodoroSessionResponse:
    cycle_progress = session.elapsed_seconds / session.target_seconds if session.target_seconds else 0.0
    pomodoro_seconds = session.target_seconds if session.target_seconds else 1
    item_pomodoros_completed = item.focus_seconds_total / pomodoro_seconds

    return PomodoroSessionResponse(
        id=session.id,
        user_id=session.user_id,
        item_id=session.item_id,
        status=session.status,
        target_seconds=session.target_seconds,
        elapsed_seconds=session.elapsed_seconds,
        credited_seconds=session.credited_seconds,
        started_at=session.started_at.isoformat(),
        paused_at=session.paused_at.isoformat() if session.paused_at else None,
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        cycle_progress=round(cycle_progress, 4),
        item_focus_seconds_total=item.focus_seconds_total,
        item_estimated_pomodoros=item.estimated_pomodoros,
        item_pomodoros_completed=round(item_pomodoros_completed, 4),
    )


def close_active_session(
    db: Session,
    session: PomodoroSession,
    item: Item,
    elapsed_seconds: int,
    new_status: str,
    credit_partial: bool,
) -> PomodoroSession:
    now = datetime.now(UTC)
    if credit_partial:
        credit_focus_time(session, item, elapsed_seconds)
    else:
        session.elapsed_seconds = max(0, min(elapsed_seconds, session.target_seconds))

    session.status = new_status
    session.ended_at = now
    session.paused_at = None
    db.add(session)
    db.add(item)
    return session


def start_session(db: Session, user_id: UUID, item_id: UUID) -> PomodoroSessionResponse:
    item = get_task_item(db, user_id, item_id)
    settings = get_or_create_settings(db, user_id)

    active_session = get_active_session(db, user_id)
    if active_session:
        active_item = db.get(Item, active_session.item_id)
        if active_item:
            close_active_session(
                db,
                active_session,
                active_item,
                active_session.elapsed_seconds,
                "abandoned",
                credit_partial=True,
            )

    now = datetime.now(UTC)
    session = PomodoroSession(
        user_id=user_id,
        item_id=item_id,
        status="running",
        target_seconds=settings.work_minutes * 60,
        elapsed_seconds=0,
        credited_seconds=0,
        started_at=now,
    )

    if not item.started:
        item.started = True

    db.add(session)
    db.add(item)
    db.commit()
    db.refresh(session)
    db.refresh(item)
    return build_session_response(session, item)


def pause_session(db: Session, user_id: UUID, session_id: UUID, elapsed_seconds: int) -> PomodoroSessionResponse:
    session = get_session_for_user(db, user_id, session_id)
    if session.status != "running":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only running sessions can be paused.")

    item = get_owned_item(db, user_id, session.item_id)
    credit_focus_time(session, item, elapsed_seconds)
    session.status = "paused"
    session.paused_at = datetime.now(UTC)

    db.add(session)
    db.add(item)
    db.commit()
    db.refresh(session)
    db.refresh(item)
    return build_session_response(session, item)


def resume_session(db: Session, user_id: UUID, session_id: UUID) -> PomodoroSessionResponse:
    session = get_session_for_user(db, user_id, session_id)
    if session.status != "paused":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only paused sessions can be resumed.")

    item = get_owned_item(db, user_id, session.item_id)
    session.status = "running"
    session.paused_at = None

    db.add(session)
    db.commit()
    db.refresh(session)
    return build_session_response(session, item)


def sync_session(db: Session, user_id: UUID, session_id: UUID, elapsed_seconds: int) -> PomodoroSessionResponse:
    session = get_session_for_user(db, user_id, session_id)
    if session.status != "running":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only running sessions can be synced.")

    item = get_owned_item(db, user_id, session.item_id)
    credit_focus_time(session, item, elapsed_seconds)

    db.add(session)
    db.add(item)
    db.commit()
    db.refresh(session)
    db.refresh(item)
    return build_session_response(session, item)


def complete_session(db: Session, user_id: UUID, session_id: UUID, elapsed_seconds: int) -> PomodoroSessionResponse:
    session = get_session_for_user(db, user_id, session_id)
    if session.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already finished.")

    item = get_owned_item(db, user_id, session.item_id)
    final_elapsed = min(max(elapsed_seconds, session.elapsed_seconds), session.target_seconds)
    credit_focus_time(session, item, final_elapsed)
    session.status = "completed"
    session.ended_at = datetime.now(UTC)
    session.paused_at = None

    db.add(session)
    db.add(item)
    db.commit()
    db.refresh(session)
    db.refresh(item)
    return build_session_response(session, item)


def abandon_session(
    db: Session,
    user_id: UUID,
    session_id: UUID,
    elapsed_seconds: int,
    credit_partial: bool,
) -> PomodoroSessionResponse:
    session = get_session_for_user(db, user_id, session_id)
    if session.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already finished.")

    item = get_owned_item(db, user_id, session.item_id)
    close_active_session(db, session, item, elapsed_seconds, "abandoned", credit_partial)

    db.commit()
    db.refresh(session)
    db.refresh(item)
    return build_session_response(session, item)


def get_active_session_response(db: Session, user_id: UUID) -> PomodoroSessionResponse | None:
    session = get_active_session(db, user_id)
    if not session:
        return None

    item = db.get(Item, session.item_id)
    if not item:
        return None

    return build_session_response(session, item)


def list_sessions(db: Session, user_id: UUID, limit: int = 20) -> list[PomodoroSessionResponse]:
    sessions = list(
        db.scalars(
            select(PomodoroSession)
            .where(PomodoroSession.user_id == user_id)
            .order_by(PomodoroSession.started_at.desc())
            .limit(limit)
        ).all()
    )

    responses: list[PomodoroSessionResponse] = []
    for session in sessions:
        item = db.get(Item, session.item_id)
        if item:
            responses.append(build_session_response(session, item))
    return responses
