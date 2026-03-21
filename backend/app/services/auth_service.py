"""Authentication: credentials, Google token, sessions."""
import os
import uuid
from datetime import timedelta

from google.auth.transport.requests import Request
from google.oauth2 import id_token
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.dependencies import now_utc
from app.models import Session as DbSession, User
from app.services.errors import ServiceError

SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "14"))


def user_public_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_admin": user.is_admin,
    }


def authenticate_password(db_session: Session, email: str, password: str) -> User:
    row_user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not row_user or not verify_password(password, row_user.password_hash):
        raise ServiceError(401, "Invalid email or password")
    return row_user


def issue_session(db_session: Session, user_id: int) -> tuple[str, object]:
    """Returns (session_id, expires_at naive datetime)."""
    session_id = str(uuid.uuid4())
    expires_at = now_utc() + timedelta(days=SESSION_TTL_DAYS)
    new_session = DbSession(id=session_id, user_id=user_id, expires_at=expires_at.replace(tzinfo=None))
    db_session.add(new_session)
    db_session.commit()
    return session_id, expires_at


def google_sign_in(db_session: Session, credential: str, google_client_id: str) -> User:
    if not google_client_id:
        raise ServiceError(503, "Google sign-in is not configured")

    try:
        token_data = id_token.verify_oauth2_token(credential, Request(), google_client_id)
    except Exception:
        raise ServiceError(401, "Invalid Google credential")

    issuer = token_data.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ServiceError(401, "Invalid token issuer")

    if not token_data.get("email_verified"):
        raise ServiceError(401, "Google email is not verified")

    google_sub = token_data.get("sub")
    email = token_data.get("email")
    if not google_sub or not email:
        raise ServiceError(401, "Invalid Google token payload")

    display_name = token_data.get("name") or email.split("@")[0]

    user = db_session.execute(select(User).where(User.google_sub == google_sub)).scalar_one_or_none()

    if not user:
        user = db_session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user and not user.google_sub:
            user.google_sub = google_sub
            db_session.commit()
            db_session.refresh(user)
        elif user and user.google_sub != google_sub:
            raise ServiceError(409, "Email already linked to a different Google account")
        else:
            user = User(
                email=email,
                google_sub=google_sub,
                password_hash="GOOGLE_AUTH_ONLY",
                display_name=display_name,
                is_admin=False,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

    return user


def destroy_session(db_session: Session, session_id: str | None) -> None:
    if session_id:
        db_session.execute(delete(DbSession).where(DbSession.id == session_id))
        db_session.commit()
