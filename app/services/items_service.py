from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.week_utils import (
    EVERGREEN_WHERE,
    get_week_end,
    get_week_start,
    is_current_week,
    is_item_overdue,
    scheduled_date_for_where,
    where_for_scheduled_date,
)


def resolve_scheduled_date(
    where: str | None,
    week_start: date | None,
    explicit_scheduled_date: date | None,
) -> date | None:
    if where in EVERGREEN_WHERE:
        return None
    if explicit_scheduled_date:
        return explicit_scheduled_date
    if week_start and where:
        return scheduled_date_for_where(week_start, where)
    return None


def list_planner_items(db: Session, user_id: UUID, week_start: date | None = None) -> list[Item]:
    today = date.today()
    week_start = week_start or get_week_start(today)
    week_end = get_week_end(week_start)

    week_filter = (Item.scheduled_date >= week_start) & (Item.scheduled_date <= week_end)
    evergreen_filter = Item.where.in_(tuple(EVERGREEN_WHERE))
    query_filter = or_(week_filter, evergreen_filter)

    if is_current_week(week_start, today):
        overdue_filter = (
            Item.scheduled_date.is_not(None)
            & (Item.scheduled_date < today)
            & (Item.finished.is_(False))
            & (Item.canceled.is_(False))
            & (~Item.where.in_(tuple(EVERGREEN_WHERE)))
            & ((Item.type.is_(None)) | (Item.type != "note"))
            & ((Item.scheduled_date < week_start) | (Item.scheduled_date > week_end))
        )
        query_filter = or_(week_filter, evergreen_filter, overdue_filter)

    return list(
        db.scalars(
            select(Item).where(Item.user_id == user_id, query_filter).order_by(Item.scheduled_date, Item.description)
        ).all()
    )


def apply_item_fields(
    item: Item,
    payload: ItemCreate | ItemUpdate,
    week_start: date | None = None,
) -> None:
    item.description = payload.description
    item.type = payload.type
    item.where = payload.where if isinstance(payload.where, str) else (payload.where[0] if payload.where else None)
    item.obs = payload.obs

    if isinstance(payload, ItemUpdate) and payload.estimated_pomodoros is not None:
        item.estimated_pomodoros = payload.estimated_pomodoros
    elif isinstance(payload, ItemCreate):
        item.estimated_pomodoros = payload.estimated_pomodoros if payload.estimated_pomodoros is not None else 1.0

    resolved_week_start = week_start or payload.week_start
    if payload.scheduled_date is not None or resolved_week_start is not None or item.where:
        item.scheduled_date = resolve_scheduled_date(item.where, resolved_week_start, payload.scheduled_date)


def create_items(db: Session, user_id: UUID, payload: ItemCreate) -> list[Item]:
    where_values = payload.where if isinstance(payload.where, list) else [payload.where]
    created_items: list[Item] = []

    for where_value in filter(None, where_values):
        scheduled_date = resolve_scheduled_date(where_value, payload.week_start, payload.scheduled_date)
        item = Item(
            user_id=user_id,
            description=payload.description,
            type=payload.type,
            where=where_value,
            scheduled_date=scheduled_date,
            obs=payload.obs,
            started=False,
            finished=False,
            important=False,
            canceled=False,
            estimated_pomodoros=payload.estimated_pomodoros if payload.estimated_pomodoros is not None else 1.0,
        )
        db.add(item)
        created_items.append(item)

    return created_items


def reschedule_item(db: Session, item: Item, scheduled_date: date, where: str | None, week_start: date) -> Item:
    if item.finished or item.canceled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reschedule a finished or canceled item.")

    if item.scheduled_date and is_item_overdue(
        item.scheduled_date,
        item.finished,
        item.canceled,
        item.type,
        item.where,
    ):
        item.carried_from = item.scheduled_date

    item.scheduled_date = scheduled_date
    item.where = where or where_for_scheduled_date(week_start, scheduled_date) or item.where
    return item


def clear_week_items(db: Session, user_id: UUID, week_start: date) -> int:
    week_end = get_week_end(week_start)
    items = list(
        db.scalars(
            select(Item).where(
                Item.user_id == user_id,
                Item.scheduled_date >= week_start,
                Item.scheduled_date <= week_end,
            )
        ).all()
    )
    for item in items:
        db.delete(item)
    return len(items)
