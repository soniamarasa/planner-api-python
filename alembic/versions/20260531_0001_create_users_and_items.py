"""create users and items

Revision ID: 20260531_0001
Revises:
Create Date: 2026-05-31 21:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260531_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password", sa.String(length=255), nullable=False),
            sa.Column("birthdate", sa.Date(), nullable=True),
            sa.Column("gender", sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    user_indexes = {index["name"] for index in inspector.get_indexes("users")}
    if op.f("ix_users_email") not in user_indexes:
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    if "items" not in existing_tables:
        op.create_table(
            "items",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("type", sa.String(length=80), nullable=True),
            sa.Column("where", sa.String(length=80), nullable=True),
            sa.Column("obs", sa.Text(), nullable=True),
            sa.Column("started", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("finished", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("important", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("canceled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    item_indexes = {index["name"] for index in inspector.get_indexes("items")}
    if op.f("ix_items_user_id") not in item_indexes:
        op.create_index(op.f("ix_items_user_id"), "items", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_items_user_id"), table_name="items")
    op.drop_table("items")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")