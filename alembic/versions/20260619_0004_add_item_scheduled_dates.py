"""add scheduled dates and week support to items

Revision ID: 20260619_0004
Revises: 20260618_0003
Create Date: 2026-06-19 10:00:00
"""

from __future__ import annotations

from datetime import date, timedelta

from alembic import op
import sqlalchemy as sa

revision = "20260619_0004"
down_revision = "20260618_0003"
branch_labels = None
depends_on = None

WEEKDAY_CODES = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "items" not in existing_tables:
        return

    item_columns = {column["name"] for column in inspector.get_columns("items")}

    if "scheduled_date" not in item_columns:
        op.add_column("items", sa.Column("scheduled_date", sa.Date(), nullable=True))
    if "carried_from" not in item_columns:
        op.add_column("items", sa.Column("carried_from", sa.Date(), nullable=True))
    if "created_at" not in item_columns:
        op.add_column(
            "items",
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if "updated_at" not in item_columns:
        op.add_column(
            "items",
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    item_indexes = {index["name"] for index in inspector.get_indexes("items")}
    if op.f("ix_items_scheduled_date") not in item_indexes:
        op.create_index(op.f("ix_items_scheduled_date"), "items", ["scheduled_date"], unique=False)

    week_start = date.today() - timedelta(days=date.today().weekday())
    items_table = sa.table(
        "items",
        sa.column("where", sa.String),
        sa.column("scheduled_date", sa.Date),
    )

    for code, offset in WEEKDAY_CODES.items():
        op.execute(
            items_table.update()
            .where(items_table.c.where == code, items_table.c.scheduled_date.is_(None))
            .values(scheduled_date=week_start + timedelta(days=offset))
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "items" not in existing_tables:
        return

    item_columns = {column["name"] for column in inspector.get_columns("items")}
    item_indexes = {index["name"] for index in inspector.get_indexes("items")}

    if op.f("ix_items_scheduled_date") in item_indexes:
        op.drop_index(op.f("ix_items_scheduled_date"), table_name="items")
    if "updated_at" in item_columns:
        op.drop_column("items", "updated_at")
    if "created_at" in item_columns:
        op.drop_column("items", "created_at")
    if "carried_from" in item_columns:
        op.drop_column("items", "carried_from")
    if "scheduled_date" in item_columns:
        op.drop_column("items", "scheduled_date")
