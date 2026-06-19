import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
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
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    carried_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    obs: Mapped[str | None] = mapped_column(Text, nullable=True)
    started: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    focus_seconds_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_pomodoros: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="items")
    pomodoro_sessions = relationship("PomodoroSession", back_populates="item", cascade="all, delete-orphan")
