"""
Shared dependencies for FastAPI routes.
"""
from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import SESSION_COOKIE_NAME
from app.db import SessionLocal
from app.models import Session as DbSession, User

COOKIE_NAME = SESSION_COOKIE_NAME


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def get_current_user(
    db_session: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User:
    """
    Dependency that validates session and returns the current user.
    Raises 401 if not authenticated.
    """
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    row = db_session.execute(
        select(DbSession, User)
        .join(User, User.id == DbSession.user_id)
        .where(DbSession.id == session_id)
    ).one_or_none()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid session")

    row_session, current_user = row
    expires_at = row_session.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now_utc():
        db_session.execute(delete(DbSession).where(DbSession.id == session_id))
        db_session.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    return current_user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires the current user to be an admin."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
