from sqlalchemy import select

from app.models import User
from app.services import bootstrap


class TestBootstrapService:
    def test_ensure_default_users_creates_and_corrects_roles(self, db_session, monkeypatch):
        class SessionWrapper:
            def __init__(self, inner):
                self.inner = inner

            def __getattr__(self, name):
                return getattr(self.inner, name)

            def close(self):
                return None

        monkeypatch.setattr(bootstrap, "SessionLocal", lambda: SessionWrapper(db_session))
        monkeypatch.setattr(bootstrap, "DEFAULT_USER_EMAIL", "default-user@dicto.es")
        monkeypatch.setattr(bootstrap, "DEFAULT_ADMIN_EMAIL", "default-admin@dicto.es")
        monkeypatch.setattr(bootstrap, "DEFAULT_USER_PASSWORD", "pw")
        monkeypatch.setattr(bootstrap, "DEFAULT_ADMIN_PASSWORD", "pw")

        bootstrap.ensure_default_users()

        test_user = db_session.execute(
            select(User).where(User.email == "default-user@dicto.es")
        ).scalar_one()
        admin_user = db_session.execute(
            select(User).where(User.email == "default-admin@dicto.es")
        ).scalar_one()
        assert test_user.is_admin is False
        assert admin_user.is_admin is True

        test_user.is_admin = True
        admin_user.is_admin = False
        db_session.commit()

        bootstrap.ensure_default_users()
        db_session.refresh(test_user)
        db_session.refresh(admin_user)
        assert test_user.is_admin is False
        assert admin_user.is_admin is True
