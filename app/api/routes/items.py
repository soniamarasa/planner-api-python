from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.item import Item
from app.models.user import User
from app.schemas.item import (
    ItemCreate,
    ItemReschedule,
    ItemResponse,
    ItemStatusUpdate,
    ItemUpdate,
    MessageResponse,
    build_item_response,
)
from app.services.focus_service import get_or_create_settings
from app.services.items_service import (
    apply_item_fields,
    clear_week_items,
    create_items,
    list_planner_items,
    reschedule_item,
)
from app.services.week_utils import get_week_start

router = APIRouter()


@router.get("/getItems/{user_id}", response_model=list[ItemResponse])
def get_items(
    user_id: UUID,
    week_start: date | None = Query(default=None),
    all_items: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[ItemResponse]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")

    settings = get_or_create_settings(db, user_id)
    today = date.today()
    if all_items:
        items = list(db.scalars(select(Item).where(Item.user_id == user_id).order_by(Item.scheduled_date, Item.description)).all())
    else:
        resolved_week_start = week_start or get_week_start(today)
        items = list_planner_items(db, user_id, resolved_week_start)
    return [build_item_response(item, settings.work_minutes, today) for item in items]


@router.get("/getItems/{user_id}/{where_value}", response_model=list[ItemResponse])
def get_items_by_where(
    user_id: UUID,
    where_value: str,
    week_start: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[ItemResponse]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")

    settings = get_or_create_settings(db, user_id)
    today = date.today()
    resolved_week_start = week_start or get_week_start(today)
    items = [
        item
        for item in list_planner_items(db, user_id, resolved_week_start)
        if item.where == where_value
    ]
    return [build_item_response(item, settings.work_minutes, today) for item in items]


@router.post("/postItem/{user_id}", response_model=list[ItemResponse])
def create_item(
    user_id: UUID,
    payload: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[ItemResponse]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to create these items.")

    if payload.week_start is None:
        where_values = payload.where if isinstance(payload.where, list) else [payload.where]
        if any(value for value in where_values if value and value not in {"todo", "notes"}):
            payload = payload.model_copy(update={"week_start": get_week_start()})

    created_items = create_items(db, user_id, payload)
    db.commit()
    for item in created_items:
        db.refresh(item)

    settings = get_or_create_settings(db, user_id)
    today = date.today()
    return [build_item_response(item, settings.work_minutes, today) for item in created_items]


@router.put("/editItem/{user_id}/{item_id}", response_model=ItemResponse)
def edit_item(
    user_id: UUID,
    item_id: UUID,
    payload: ItemUpdate,
    week_start: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ItemResponse:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if current_user.id != user_id or item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to edit this item.")

    resolved_week_start = week_start or payload.week_start or (
        get_week_start(item.scheduled_date) if item.scheduled_date else get_week_start()
    )
    apply_item_fields(item, payload, resolved_week_start)

    db.add(item)
    db.commit()
    db.refresh(item)
    settings = get_or_create_settings(db, user_id)
    return build_item_response(item, settings.work_minutes)


@router.put("/rescheduleItem/{user_id}/{item_id}", response_model=ItemResponse)
def reschedule_item_route(
    user_id: UUID,
    item_id: UUID,
    payload: ItemReschedule,
    week_start: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ItemResponse:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if current_user.id != user_id or item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to reschedule this item.")

    resolved_week_start = week_start or get_week_start(payload.scheduled_date)
    reschedule_item(db, item, payload.scheduled_date, payload.where, resolved_week_start)
    db.add(item)
    db.commit()
    db.refresh(item)
    settings = get_or_create_settings(db, user_id)
    return build_item_response(item, settings.work_minutes)


@router.put("/updateStatus/{user_id}/{item_id}", response_model=ItemResponse)
def update_status(
    user_id: UUID,
    item_id: UUID,
    payload: ItemStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ItemResponse:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if current_user.id != user_id or item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to change the status of this item.")

    for field in ("started", "finished", "important", "canceled"):
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value)

    db.add(item)
    db.commit()
    db.refresh(item)
    settings = get_or_create_settings(db, user_id)
    return build_item_response(item, settings.work_minutes)


@router.delete("/deleteItem/{user_id}/{item_id}", response_model=MessageResponse)
def delete_item(
    user_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MessageResponse:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if current_user.id != user_id or item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete this item.")

    db.delete(item)
    db.commit()
    return MessageResponse(message="Successfully deleted item!")


@router.delete("/{user_id}/week", response_model=MessageResponse)
def clear_week(
    user_id: UUID,
    week_start: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MessageResponse:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete these items.")

    deleted_count = clear_week_items(db, user_id, week_start)
    db.commit()
    return MessageResponse(message=f"Cleared {deleted_count} item(s) from the selected week.")


@router.delete("/{user_id}/reset", response_model=MessageResponse)
def reset_data(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MessageResponse:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete these items.")

    items = list(db.scalars(select(Item).where(Item.user_id == user_id)).all())
    for item in items:
        db.delete(item)
    db.commit()
    return MessageResponse(message="Items were successfully deleted")
