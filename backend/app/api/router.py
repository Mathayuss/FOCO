from fastapi import APIRouter
from app.api.endpoints import health, analytics, imports

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(analytics.router)
api_router.include_router(imports.router)
