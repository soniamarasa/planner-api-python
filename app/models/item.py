import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    where: Mapped[str | None] = mapped_column(String(80), nullable=True)
    obs: Mapped[str | None] = mapped_column(Text, nullable=True)
    started: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="items")
