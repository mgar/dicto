"""
Authentication routes: login, logout, me.
"""
import os

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session

from app.dependencies import COOKIE_NAME, get_current_user, get_db, now_utc
from app.models import User
from app.schemas import GoogleSignInRequest, LoginRequest
from app.services import auth_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def set_session_cookie(resp: Response, session_id: str, expires_at) -> None:
    """Set the session cookie on the response."""
    max_age = int((expires_at - now_utc()).total_seconds())
    resp.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def clear_session_cookie(resp: Response) -> None:
    """Clear the session cookie."""
    resp.delete_cookie(key=COOKIE_NAME, path="/")


@router.post("/login")
def login(payload: LoginRequest, resp: Response, db_session: Session = Depends(get_db)):
    """Authenticate user and create session."""
    try:
        row_user = auth_service.authenticate_password(db_session, payload.email, payload.password)
        session_id, expires_at = auth_service.issue_session(db_session, row_user.id)
    except ServiceError as err:
        raise_http(err)
    set_session_cookie(resp, session_id, expires_at)
    return {"user": auth_service.user_public_dict(row_user)}


@router.post("/google")
def google_login(payload: GoogleSignInRequest, resp: Response, db_session: Session = Depends(get_db)):
    """Authenticate user with a Google ID token and create a session cookie."""
    try:
        row_user = auth_service.google_sign_in(db_session, payload.credential, GOOGLE_CLIENT_ID)
        session_id, expires_at = auth_service.issue_session(db_session, row_user.id)
    except ServiceError as err:
        raise_http(err)
    set_session_cookie(resp, session_id, expires_at)
    return {"user": auth_service.user_public_dict(row_user)}


@router.post("/logout")
def logout(
    resp: Response,
    db_session: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=COOKIE_NAME),
):
    """Log out user and clear session."""
    auth_service.destroy_session(db_session, session_id)
    clear_session_cookie(resp)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return {"user": auth_service.user_public_dict(user)}
