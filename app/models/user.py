import uuid

from sqlalchemy import Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    birthdate: Mapped[Date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)

    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")
    focus_settings = relationship(
        "FocusSettings",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    pomodoro_sessions = relationship(
        "PomodoroSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
