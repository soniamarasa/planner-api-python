from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemStatusUpdate, ItemUpdate, MessageResponse

router = APIRouter()


@router.get("/getItems/{user_id}", response_model=list[ItemResponse])
def get_items(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[Item]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")

    return list(db.scalars(select(Item).where(Item.user_id == user_id)).all())


@router.get("/getItems/{user_id}/{where_value}", response_model=list[ItemResponse])
def get_items_by_where(
    user_id: UUID,
    where_value: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[Item]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")

    return list(
        db.scalars(select(Item).where(Item.user_id == user_id, Item.where == where_value)).all()
    )


@router.post("/postItem/{user_id}", response_model=list[ItemResponse])
def create_item(
    user_id: UUID,
    payload: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[Item]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to create these items.")

    where_values = payload.where if isinstance(payload.where, list) else [payload.where]
    created_items: list[Item] = []
    for where_value in filter(None, where_values):
        item = Item(
            user_id=user_id,
            description=payload.description,
            type=payload.type,
            where=where_value,
            obs=payload.obs,
            started=False,
            finished=False,
            important=False,
            canceled=False,
        )
        db.add(item)
        created_items.append(item)

    db.commit()
    for item in created_items:
        db.refresh(item)
    return created_items


@router.put("/editItem/{user_id}/{item_id}", response_model=ItemResponse)
def edit_item(
    user_id: UUID,
    item_id: UUID,
    payload: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Item:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    if current_user.id != user_id or item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to edit this item.")

    item.description = payload.description
    item.type = payload.type
    item.where = payload.where if isinstance(payload.where, str) else (payload.where[0] if payload.where else None)
    item.obs = payload.obs

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/updateStatus/{user_id}/{item_id}", response_model=ItemResponse)
def update_status(
    user_id: UUID,
    item_id: UUID,
    payload: ItemStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Item:
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
    return item


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
