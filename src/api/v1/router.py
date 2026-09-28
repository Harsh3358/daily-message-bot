"""API v1 master router."""
from fastapi import APIRouter
from src.api.v1.deliveries import router as deliveries_router
from src.api.v1.health import router as health_router
from src.api.v1.problems import router as problems_router
from src.api.v1.subjects import router as subjects_router
from src.api.v1.telegram_groups import router as telegram_groups_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(subjects_router)
api_v1_router.include_router(problems_router)
api_v1_router.include_router(telegram_groups_router)
api_v1_router.include_router(deliveries_router)
