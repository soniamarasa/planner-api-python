"""add focus settings and pomodoro sessions

Revision ID: 20260618_0002
Revises: 20260531_0001
Create Date: 2026-06-18 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260618_0002"
down_revision = "20260531_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "items" in existing_tables:
        item_columns = {column["name"] for column in inspector.get_columns("items")}
        if "focus_seconds_total" not in item_columns:
            op.add_column(
                "items",
                sa.Column("focus_seconds_total", sa.Integer(), nullable=False, server_default="0"),
            )
        if "estimated_pomodoros" not in item_columns:
            op.add_column(
                "items",
                sa.Column("estimated_pomodoros", sa.Float(), nullable=False, server_default="1"),
            )

    if "focus_settings" not in existing_tables:
        op.create_table(
            "focus_settings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("work_minutes", sa.Integer(), nullable=False, server_default="25"),
            sa.Column("short_break_minutes", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("long_break_minutes", sa.Integer(), nullable=False, server_default="15"),
            sa.Column("long_break_interval", sa.Integer(), nullable=False, server_default="4"),
            sa.Column("ambient_sound", sa.String(length=50), nullable=False, server_default="rain"),
            sa.Column("sound_volume", sa.Float(), nullable=False, server_default="0.5"),
            sa.Column("auto_start_breaks", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("auto_start_focus", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("notify_on_complete", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(op.f("ix_focus_settings_user_id"), "focus_settings", ["user_id"], unique=True)

    if "pomodoro_sessions" not in existing_tables:
        op.create_table(
            "pomodoro_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
            sa.Column("target_seconds", sa.Integer(), nullable=False),
            sa.Column("elapsed_seconds", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("credited_seconds", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_pomodoro_sessions_user_id"), "pomodoro_sessions", ["user_id"], unique=False)
        op.create_index(op.f("ix_pomodoro_sessions_item_id"), "pomodoro_sessions", ["item_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "pomodoro_sessions" in existing_tables:
        op.drop_index(op.f("ix_pomodoro_sessions_item_id"), table_name="pomodoro_sessions")
        op.drop_index(op.f("ix_pomodoro_sessions_user_id"), table_name="pomodoro_sessions")
        op.drop_table("pomodoro_sessions")

    if "focus_settings" in existing_tables:
        op.drop_index(op.f("ix_focus_settings_user_id"), table_name="focus_settings")
        op.drop_table("focus_settings")

    if "items" in existing_tables:
        item_columns = {column["name"] for column in inspector.get_columns("items")}
        if "estimated_pomodoros" in item_columns:
            op.drop_column("items", "estimated_pomodoros")
        if "focus_seconds_total" in item_columns:
            op.drop_column("items", "focus_seconds_total")
