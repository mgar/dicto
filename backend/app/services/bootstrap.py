from sqlalchemy import select

from app.core.config import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_USER_EMAIL,
    DEFAULT_USER_PASSWORD,
)
from app.core.security import hash_password
from app.db import SessionLocal
from app.models import User


def ensure_default_users() -> None:
    """Create default test and admin users if they don't exist."""
    db_session = SessionLocal()
    try:
        test_user = db_session.execute(select(User).where(User.email == DEFAULT_USER_EMAIL)).scalar_one_or_none()
        if not test_user:
            db_session.add(
                User(
                    email=DEFAULT_USER_EMAIL,
                    password_hash=hash_password(DEFAULT_USER_PASSWORD),
                    display_name="Test User",
                    is_admin=False,
                )
            )
        elif test_user.is_admin:
            test_user.is_admin = False

        admin_user = db_session.execute(select(User).where(User.email == DEFAULT_ADMIN_EMAIL)).scalar_one_or_none()
        if not admin_user:
            db_session.add(
                User(
                    email=DEFAULT_ADMIN_EMAIL,
                    password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                    display_name="Admin",
                    is_admin=True,
                )
            )
        elif not admin_user.is_admin:
            admin_user.is_admin = True

        db_session.commit()
    finally:
        db_session.close()
