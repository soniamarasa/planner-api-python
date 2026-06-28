"""add focus ambient_mix

Revision ID: 20260628_0006
Revises: 20260619_0005
Create Date: 2026-06-28 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260628_0006"
down_revision = "20260619_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "focus_settings" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("focus_settings")}
        if "ambient_mix" not in columns:
            op.add_column(
                "focus_settings",
                sa.Column(
                    "ambient_mix",
                    postgresql.JSONB(astext_type=sa.Text()),
                    nullable=False,
                    server_default="[]",
                ),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "focus_settings" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("focus_settings")}
        if "ambient_mix" in columns:
            op.drop_column("focus_settings", "ambient_mix")
