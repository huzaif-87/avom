"""Main application entry point for TalentRank AI backend."""

import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Optimize PyTorch CPU execution for containerized cloud environments (e.g. Render 512MB RAM)
try:
    import torch
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
except Exception:
    pass

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.database import connect_to_mongo, close_mongo_connection



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize and cleanup resources."""
    # Startup: Connect to MongoDB
    await connect_to_mongo()
    yield
    # Shutdown: Close MongoDB connection
    await close_mongo_connection()


def create_application() -> FastAPI:
    """Initialize and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API for TalentRank AI - Resume Matching & Candidate Ranking System",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )


    # Configure CORS for local React frontend and deployed production frontends
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.ENVIRONMENT == "production" else settings.CORS_ORIGINS,
        allow_origin_regex=r"https://.*\.vercel\.app" if settings.ENVIRONMENT == "production" else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register error handlers
    register_error_handlers(application)

    # Include modular API router under /api
    application.include_router(api_router, prefix=settings.API_PREFIX)

    @application.get(
        "/",
        tags=["Root"],
        summary="API Root Information",
        description="Root informational endpoint providing API metadata.",
    )
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs",
            "health_check": f"{settings.API_PREFIX}/health",
        }

    return application


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
