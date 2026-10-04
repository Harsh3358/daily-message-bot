"""Application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.api.v1.router import api_v1_router
from src.core.config import get_settings
from src.core.exceptions import AppException, DuplicateEntityException, EntityNotFoundException
from src.core.logging import setup_logging
from src.scheduler import shutdown_scheduler, start_scheduler

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Starts APScheduler on startup and shuts it down cleanly when the process exits.
    """
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade automated daily technical question delivery service for Telegram groups.",
    version="1.0.0",
    lifespan=lifespan,
)


# Exception handlers
@app.exception_handler(EntityNotFoundException)
async def handle_entity_not_found(_request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "error": "NOT_FOUND", "context": exc.details},
    )


@app.exception_handler(DuplicateEntityException)
async def handle_duplicate_entity(_request: Request, exc: DuplicateEntityException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message, "error": "CONFLICT", "context": exc.details},
    )


@app.exception_handler(AppException)
async def handle_app_exception(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "error": "BAD_REQUEST", "context": exc.details},
    )


from fastapi.responses import JSONResponse, RedirectResponse

# Include API Routers
app.include_router(api_v1_router)

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect the root URL to the Swagger documentation."""
    return RedirectResponse(url="/docs")
