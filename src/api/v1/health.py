"""Health and readiness check endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import get_settings
from src.core.database import get_db_session

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", status_code=status.HTTP_200_OK, summary="Application health status")
async def health_check(session: AsyncSession = Depends(get_db_session)):
    """Check application health and PostgreSQL database connectivity."""
    db_status = "healthy"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as err:
        db_status = f"unhealthy: {str(err)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timezone": settings.APP_TIMEZONE,
    }
