import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FocusSettings(Base):
    __tablename__ = "focus_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    work_minutes: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    short_break_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    long_break_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    long_break_interval: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    ambient_sound: Mapped[str] = mapped_column(String(50), default="rain", nullable=False)
    sound_volume: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    ambient_mix: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)
    background_id: Mapped[str] = mapped_column(String(50), default="forest", nullable=False)
    auto_start_breaks: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_start_focus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_on_complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="focus_settings")
