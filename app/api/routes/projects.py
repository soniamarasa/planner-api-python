from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.item import ItemResponse, build_item_response
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, UnassignedSummary
from app.services.focus_service import get_or_create_settings
from app.services.projects_service import (
    count_unassigned_open_tasks,
    create_project,
    get_project,
    get_project_response,
    list_project_items,
    list_projects,
    list_unassigned_items,
    update_project,
)

router = APIRouter()


@router.get("/getProjects/{user_id}", response_model=list[ProjectResponse])
def get_projects(
    user_id: UUID,
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[ProjectResponse]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these projects.")
    return list_projects(db, user_id, include_archived)


@router.post("/postProject/{user_id}", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def post_project(
    user_id: UUID,
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ProjectResponse:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to create projects.")

    project = create_project(db, user_id, payload)
    db.commit()
    db.refresh(project)
    return get_project_response(db, user_id, project.id)


@router.put("/editProject/{user_id}/{project_id}", response_model=ProjectResponse)
def edit_project(
    user_id: UUID,
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ProjectResponse:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to edit projects.")

    project = get_project(db, user_id, project_id)
    update_project(db, project, payload)
    db.commit()
    db.refresh(project)
    return get_project_response(db, user_id, project.id)


@router.get("/getProjectItems/{user_id}/{project_id}", response_model=list[ItemResponse])
def get_project_items(
    user_id: UUID,
    project_id: UUID,
    include_finished: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[ItemResponse]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")

    get_project(db, user_id, project_id)
    settings = get_or_create_settings(db, user_id)
    items = list_project_items(db, user_id, project_id, include_finished)
    return [build_item_response(item, settings.work_minutes) for item in items]


@router.get("/getUnassignedSummary/{user_id}", response_model=UnassignedSummary)
def get_unassigned_summary(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> UnassignedSummary:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")
    return UnassignedSummary(open_count=count_unassigned_open_tasks(db, user_id))


@router.get("/getUnassignedItems/{user_id}", response_model=list[ItemResponse])
def get_unassigned_items(
    user_id: UUID,
    include_finished: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[ItemResponse]:
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access these items.")

    settings = get_or_create_settings(db, user_id)
    items = list_unassigned_items(db, user_id, include_finished)
    return [build_item_response(item, settings.work_minutes) for item in items]
