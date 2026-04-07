"""
dicto API - Main application entry point.

This module sets up the FastAPI application, middleware, and includes all routers.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import API_CORS_ORIGIN, is_testing
from app.internal import admin_router
from app.routers import (
    auth_router,
    grammar_router,
    learn_router,
    reviews_router,
    stats_router,
    vocab_router,
)
from app.services.bootstrap import ensure_default_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not is_testing():
        from alembic.config import Config
        from alembic import command as alembic_command

        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
        alembic_command.upgrade(alembic_cfg, "head")

        ensure_default_users()
        from app.services.seed_service import seed_content
        seed_content()
    yield


# Create FastAPI app
app = FastAPI(
    title="dicto API",
    description="Spanish learning application with spaced repetition",
    version="0.4.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[API_CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(grammar_router)
app.include_router(vocab_router)
app.include_router(learn_router)
app.include_router(reviews_router)
app.include_router(stats_router)
app.include_router(admin_router)


# -----------------------
# Health check
# -----------------------
@app.get("/api/health", tags=["health"])
def health():
    """Health check endpoint."""
    return {"ok": True}
