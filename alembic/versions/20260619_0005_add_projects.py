"""add projects and item project_id

Revision ID: 20260619_0005
Revises: 20260619_0004
Create Date: 2026-06-19 14:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260619_0005"
down_revision = "20260619_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "projects" not in existing_tables:
        op.create_table(
            "projects",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("icon", sa.String(length=80), nullable=False, server_default="pi-briefcase"),
            sa.Column("color", sa.String(length=20), nullable=False, server_default="#ff9a3d"),
            sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)

    if "items" in existing_tables:
        item_columns = {column["name"] for column in inspector.get_columns("items")}
        if "project_id" not in item_columns:
            op.add_column("items", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_items_project_id_projects",
                "items",
                "projects",
                ["project_id"],
                ["id"],
                ondelete="SET NULL",
            )
            op.create_index(op.f("ix_items_project_id"), "items", ["project_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "items" in existing_tables:
        item_columns = {column["name"] for column in inspector.get_columns("items")}
        item_indexes = {index["name"] for index in inspector.get_indexes("items")}
        if op.f("ix_items_project_id") in item_indexes:
            op.drop_index(op.f("ix_items_project_id"), table_name="items")
        if "project_id" in item_columns:
            op.drop_constraint("fk_items_project_id_projects", "items", type_="foreignkey")
            op.drop_column("items", "project_id")

    if "projects" in existing_tables:
        op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
        op.drop_table("projects")
