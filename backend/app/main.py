import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, Base

# Import all models so Alembic can detect them
from app.models import models  # noqa: F401

from app.api.routes import (
    auth, campaigns, contacts, upload, tracking,
    analytics, templates, export, ai, replies, audit,
)

setup_logging()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Recruiter Outreach Platform...")
    
    # Create upload directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path("/app/logs").mkdir(parents=True, exist_ok=True)
    
    # Create tables (in production use Alembic migrations)
    if settings.APP_ENV == "development":
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

    logger.info(f"Server running in {settings.APP_ENV} mode")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered recruiter outreach platform with personalized email campaigns",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads (served for internal tracking)
uploads_path = Path(settings.UPLOAD_DIR)
if uploads_path.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# API Routes
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(campaigns.router, prefix=API_PREFIX)
app.include_router(contacts.router, prefix=API_PREFIX)
app.include_router(upload.router, prefix=API_PREFIX)
app.include_router(tracking.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(templates.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(replies.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy", "version": "1.0.0", "env": settings.APP_ENV}


@app.get("/")
def root() -> dict:
    return {
        "message": "AI Recruiter Outreach Platform API",
        "docs": "/api/docs",
        "health": "/health",
    }
