from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    description: str
    type: str | None = None
    where: str | list[str] | None = None
    obs: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    pass


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
    obs: str | None
    started: bool
    finished: bool
    important: bool
    canceled: bool


class MessageResponse(BaseModel):
    message: str
