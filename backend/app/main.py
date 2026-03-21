"""
dicto API - Main application entry point.

This module sets up the FastAPI application and middleware.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth_router

# Configuration
APP_CORS_ORIGIN = os.getenv("API_CORS_ORIGIN", "http://localhost:5173")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "test@dicto.es")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "changeme")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@dicto.es")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme")

# Create FastAPI app
app = FastAPI(
    title="dicto API",
    description="Spanish learning application with spaced repetition",
    version="0.4.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[APP_CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

# -----------------------
# Health check
# -----------------------
@app.get("/api/health", tags=["health"])
def health():
    """Health check endpoint."""
    return {"ok": True}
