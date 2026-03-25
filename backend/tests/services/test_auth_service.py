import pytest
from sqlalchemy import select

from app.models import Session as DbSession
from app.services import auth_service
from app.services.errors import ServiceError
from tests.conftest import make_user


class TestAuthService:
    def test_authenticate_password_success_and_failure(self, db_session):
        user = make_user(db_session, email="svc-auth@dicto.es", password="pw123")
        authed = auth_service.authenticate_password(db_session, user.email, "pw123")
        assert authed.id == user.id

        with pytest.raises(ServiceError) as exc:
            auth_service.authenticate_password(db_session, user.email, "wrong")
        assert exc.value.status_code == 401

    def test_issue_and_destroy_session(self, db_session):
        user = make_user(db_session, email="svc-session@dicto.es", password="pw")
        session_id, _ = auth_service.issue_session(db_session, user.id)
        session_row = db_session.execute(select(DbSession).where(DbSession.id == session_id)).scalar_one_or_none()
        assert session_row is not None

        auth_service.destroy_session(db_session, session_id)
        session_row = db_session.execute(select(DbSession).where(DbSession.id == session_id)).scalar_one_or_none()
        assert session_row is None

    def test_google_sign_in_creates_user(self, db_session, monkeypatch):
        def fake_verify(_credential, _request, _audience):
            return {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-service-1",
                "email": "service-google@dicto.es",
                "email_verified": True,
                "name": "Service Google",
            }

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        user = auth_service.google_sign_in(db_session, "fake-credential", "client-id")
        assert user.email == "service-google@dicto.es"
        assert user.google_sub == "google-sub-service-1"
