"""
Tests for /api/auth endpoints: login, logout, /me.
"""
import pytest
from sqlalchemy import select

from app.models import User
from app.routers import auth as auth_router
from app.services import auth_service
from tests.conftest import make_user, make_session, COOKIE_NAME


class TestLogin:
    def test_login_success(self, client, db_session):
        make_user(db_session, email="login-a@dicto.es", password="pass123")
        response = client.post("/api/auth/login", json={"email": "login-a@dicto.es", "password": "pass123"})
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "login-a@dicto.es"
        assert data["user"]["is_admin"] is False
        assert COOKIE_NAME in response.cookies

    def test_login_wrong_password(self, client, db_session):
        make_user(db_session, email="login-b@dicto.es", password="correct")
        response = client.post("/api/auth/login", json={"email": "login-b@dicto.es", "password": "wrong"})
        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        response = client.post("/api/auth/login", json={"email": "ghost@dicto.es", "password": "x"})
        assert response.status_code == 401

    def test_login_sets_cookie(self, client, db_session):
        make_user(db_session, email="login-c@dicto.es", password="pw")
        response = client.post("/api/auth/login", json={"email": "login-c@dicto.es", "password": "pw"})
        assert COOKIE_NAME in response.cookies

    def test_login_admin_flag_propagates(self, client, db_session):
        make_user(db_session, email="admin-login@dicto.es", password="pw", is_admin=True)
        response = client.post("/api/auth/login", json={"email": "admin-login@dicto.es", "password": "pw"})
        assert response.json()["user"]["is_admin"] is True


class TestMe:
    def test_me_authenticated(self, client, db_session):
        user = make_user(db_session, email="me-authenticated@dicto.es", password="pw")
        session_id = make_session(db_session, user)
        client.cookies.set(COOKIE_NAME, session_id)
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "me-authenticated@dicto.es"

    def test_me_no_cookie(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_invalid_session_id(self, client):
        client.cookies.set(COOKIE_NAME, "not-a-real-session-id")
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_expired_session(self, client, db_session):
        user = make_user(db_session, email="expired-session@dicto.es", password="pw")
        session_id = make_session(db_session, user, expired=True)
        client.cookies.set(COOKIE_NAME, session_id)
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_expired_session_is_deleted(self, client, db_session):
        from sqlalchemy import select
        from app.models import Session as DbSession
        user = make_user(db_session, email="deleted-expired@dicto.es", password="pw")
        session_id = make_session(db_session, user, expired=True)
        client.cookies.set(COOKIE_NAME, session_id)
        client.get("/api/auth/me")
        remaining = db_session.execute(
            select(DbSession).where(DbSession.id == session_id)
        ).scalar_one_or_none()
        assert remaining is None


class TestLogout:
    def test_logout_clears_session(self, client, db_session):
        from sqlalchemy import select
        from app.models import Session as DbSession
        user = make_user(db_session, email="logout-user@dicto.es", password="pw")
        session_id = make_session(db_session, user)
        client.cookies.set(COOKIE_NAME, session_id)
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        remaining = db_session.execute(
            select(DbSession).where(DbSession.id == session_id)
        ).scalar_one_or_none()
        assert remaining is None

    def test_logout_without_session_is_ok(self, client):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200


class TestGoogleLogin:
    def test_google_login_creates_user_and_session(self, client, db_session, monkeypatch):
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "test-client-id")

        def fake_verify(_credential, _request, _audience):
            return {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-1",
                "email": "new-google@dicto.es",
                "email_verified": True,
                "name": "Google User",
            }

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        response = client.post("/api/auth/google", json={"credential": "fake-token"})
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "new-google@dicto.es"
        assert COOKIE_NAME in response.cookies

        db_user = db_session.execute(select(User).where(User.email == "new-google@dicto.es")).scalar_one()
        assert db_user.google_sub == "google-sub-1"

    def test_google_login_links_existing_email(self, client, db_session, monkeypatch):
        make_user(db_session, email="existing@dicto.es", password="pw")
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "test-client-id")

        def fake_verify(_credential, _request, _audience):
            return {
                "iss": "accounts.google.com",
                "sub": "google-sub-2",
                "email": "existing@dicto.es",
                "email_verified": True,
                "name": "Existing User",
            }

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        response = client.post("/api/auth/google", json={"credential": "fake-token"})
        assert response.status_code == 200

        db_user = db_session.execute(select(User).where(User.email == "existing@dicto.es")).scalar_one()
        assert db_user.google_sub == "google-sub-2"

    def test_google_login_invalid_credential_is_401(self, client, monkeypatch):
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "test-client-id")

        def fake_verify(_credential, _request, _audience):
            raise ValueError("invalid token")

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        response = client.post("/api/auth/google", json={"credential": "bad-token"})
        assert response.status_code == 401

    def test_google_login_not_configured_is_503(self, client, monkeypatch):
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "")
        response = client.post("/api/auth/google", json={"credential": "any"})
        assert response.status_code == 503
