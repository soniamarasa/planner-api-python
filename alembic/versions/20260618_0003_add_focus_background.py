"""add focus background_id

Revision ID: 20260618_0003
Revises: 20260618_0002
Create Date: 2026-06-18 20:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260618_0003"
down_revision = "20260618_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "focus_settings" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("focus_settings")}
        if "background_id" not in columns:
            op.add_column(
                "focus_settings",
                sa.Column("background_id", sa.String(length=50), nullable=False, server_default="forest"),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "focus_settings" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("focus_settings")}
        if "background_id" in columns:
            op.drop_column("focus_settings", "background_id")
