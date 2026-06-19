from fastapi import APIRouter

from app.api.routes import focus, items, projects, users

api_router = APIRouter()
api_router.include_router(users.router, tags=["users"])
api_router.include_router(items.router, tags=["items"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(focus.router, tags=["focus"])
