from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.item import Item
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


def _normalize_icon(icon: str) -> str:
    value = icon.strip()
    if value.startswith("pi pi-"):
        return value.replace("pi pi-", "pi-", 1)
    if value.startswith("pi-") or value == "pi":
        return value if value != "pi" else "pi-briefcase"
    if value.startswith("pi "):
        return value.replace("pi ", "pi-", 1)
    return value


def build_project_response(project: Project, open_tasks_count: int = 0, focus_seconds_total: int = 0) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        icon=project.icon,
        color=project.color,
        archived=project.archived,
        open_tasks_count=open_tasks_count,
        focus_seconds_total=focus_seconds_total,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def get_project_response(db: Session, user_id: UUID, project_id: UUID) -> ProjectResponse:
    project = get_project(db, user_id, project_id)
    stats_row = db.execute(
        select(
            func.count(Item.id).filter(Item.finished.is_(False), Item.canceled.is_(False)).label("open_tasks_count"),
            func.coalesce(func.sum(Item.focus_seconds_total), 0).label("focus_seconds_total"),
        ).where(Item.user_id == user_id, Item.project_id == project_id)
    ).one()
    return build_project_response(
        project,
        int(stats_row.open_tasks_count or 0),
        int(stats_row.focus_seconds_total or 0),
    )


def list_projects(db: Session, user_id: UUID, include_archived: bool = False) -> list[ProjectResponse]:
    query = select(Project).where(Project.user_id == user_id)
    if not include_archived:
        query = query.where(Project.archived.is_(False))
    projects = list(db.scalars(query.order_by(Project.name)).all())

    if not projects:
        return []

    project_ids = [project.id for project in projects]
    stats_rows = db.execute(
        select(
            Item.project_id,
            func.count(Item.id).filter(Item.finished.is_(False), Item.canceled.is_(False)).label("open_tasks_count"),
            func.coalesce(func.sum(Item.focus_seconds_total), 0).label("focus_seconds_total"),
        )
        .where(Item.user_id == user_id, Item.project_id.in_(project_ids))
        .group_by(Item.project_id)
    ).all()
    stats_map = {
        row.project_id: (int(row.open_tasks_count or 0), int(row.focus_seconds_total or 0))
        for row in stats_rows
    }

    return [
        build_project_response(
            project,
            stats_map.get(project.id, (0, 0))[0],
            stats_map.get(project.id, (0, 0))[1],
        )
        for project in projects
    ]


def get_project(db: Session, user_id: UUID, project_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def create_project(db: Session, user_id: UUID, payload: ProjectCreate) -> Project:
    project = Project(
        user_id=user_id,
        name=payload.name.strip(),
        icon=_normalize_icon(payload.icon),
        color=payload.color,
    )
    db.add(project)
    return project


def update_project(db: Session, project: Project, payload: ProjectUpdate) -> Project:
    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.icon is not None:
        project.icon = _normalize_icon(payload.icon)
    if payload.color is not None:
        project.color = payload.color
    if payload.archived is not None:
        project.archived = payload.archived
    db.add(project)
    return project


def list_project_items(db: Session, user_id: UUID, project_id: UUID, include_finished: bool = True) -> list[Item]:
    query = (
        select(Item)
        .options(selectinload(Item.project))
        .where(Item.user_id == user_id, Item.project_id == project_id)
    )
    if not include_finished:
        query = query.where(Item.finished.is_(False), Item.canceled.is_(False))

    return list(db.scalars(query.order_by(Item.scheduled_date.nulls_last(), Item.description)).all())


def validate_project_id(db: Session, user_id: UUID, project_id: UUID | None) -> None:
    if project_id is None:
        return
    project = db.get(Project, project_id)
    if not project or project.user_id != user_id or project.archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project.")


def count_unassigned_open_tasks(db: Session, user_id: UUID) -> int:
    from sqlalchemy import or_

    count = db.scalar(
        select(func.count(Item.id)).where(
            Item.user_id == user_id,
            Item.project_id.is_(None),
            Item.finished.is_(False),
            Item.canceled.is_(False),
            or_(Item.type.is_(None), Item.type != "note"),
        )
    )
    return int(count or 0)


def list_unassigned_items(db: Session, user_id: UUID, include_finished: bool = True) -> list[Item]:
    query = (
        select(Item)
        .options(selectinload(Item.project))
        .where(Item.user_id == user_id, Item.project_id.is_(None))
    )
    if not include_finished:
        query = query.where(Item.finished.is_(False), Item.canceled.is_(False))

    return list(db.scalars(query.order_by(Item.scheduled_date.nulls_last(), Item.description)).all())
