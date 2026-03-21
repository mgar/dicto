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
        make_user(db_session, email="a@test.com", password="pass123")
        r = client.post("/api/auth/login", json={"email": "a@test.com", "password": "pass123"})
        assert r.status_code == 200
        data = r.json()
        assert data["user"]["email"] == "a@test.com"
        assert data["user"]["is_admin"] is False
        assert COOKIE_NAME in r.cookies

    def test_login_wrong_password(self, client, db_session):
        make_user(db_session, email="b@test.com", password="correct")
        r = client.post("/api/auth/login", json={"email": "b@test.com", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_email(self, client):
        r = client.post("/api/auth/login", json={"email": "ghost@test.com", "password": "x"})
        assert r.status_code == 401

    def test_login_sets_cookie(self, client, db_session):
        make_user(db_session, email="c@test.com", password="pw")
        r = client.post("/api/auth/login", json={"email": "c@test.com", "password": "pw"})
        assert COOKIE_NAME in r.cookies

    def test_login_admin_flag_propagates(self, client, db_session):
        make_user(db_session, email="adm@test.com", password="pw", is_admin=True)
        r = client.post("/api/auth/login", json={"email": "adm@test.com", "password": "pw"})
        assert r.json()["user"]["is_admin"] is True


class TestMe:
    def test_me_authenticated(self, client, db_session):
        user = make_user(db_session, email="me@test.com", password="pw")
        session_id = make_session(db_session, user)
        client.cookies.set(COOKIE_NAME, session_id)
        r = client.get("/api/auth/me")
        assert r.status_code == 200
        assert r.json()["user"]["email"] == "me@test.com"

    def test_me_no_cookie(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_invalid_session_id(self, client):
        client.cookies.set(COOKIE_NAME, "not-a-real-session-id")
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_expired_session(self, client, db_session):
        user = make_user(db_session, email="exp@test.com", password="pw")
        session_id = make_session(db_session, user, expired=True)
        client.cookies.set(COOKIE_NAME, session_id)
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_expired_session_is_deleted(self, client, db_session):
        from sqlalchemy import select
        from app.models import Session as DbSession
        user = make_user(db_session, email="del@test.com", password="pw")
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
        user = make_user(db_session, email="out@test.com", password="pw")
        session_id = make_session(db_session, user)
        client.cookies.set(COOKIE_NAME, session_id)
        r = client.post("/api/auth/logout")
        assert r.status_code == 200
        remaining = db_session.execute(
            select(DbSession).where(DbSession.id == session_id)
        ).scalar_one_or_none()
        assert remaining is None

    def test_logout_without_session_is_ok(self, client):
        r = client.post("/api/auth/logout")
        assert r.status_code == 200


class TestGoogleLogin:
    def test_google_login_creates_user_and_session(self, client, db_session, monkeypatch):
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "test-client-id")

        def fake_verify(_credential, _request, _audience):
            return {
                "iss": "https://accounts.google.com",
                "sub": "google-sub-1",
                "email": "new-google@test.com",
                "email_verified": True,
                "name": "Google User",
            }

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        r = client.post("/api/auth/google", json={"credential": "fake-token"})
        assert r.status_code == 200
        assert r.json()["user"]["email"] == "new-google@test.com"
        assert COOKIE_NAME in r.cookies

        db_user = db_session.execute(select(User).where(User.email == "new-google@test.com")).scalar_one()
        assert db_user.google_sub == "google-sub-1"

    def test_google_login_links_existing_email(self, client, db_session, monkeypatch):
        make_user(db_session, email="existing@test.com", password="pw")
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "test-client-id")

        def fake_verify(_credential, _request, _audience):
            return {
                "iss": "accounts.google.com",
                "sub": "google-sub-2",
                "email": "existing@test.com",
                "email_verified": True,
                "name": "Existing User",
            }

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        r = client.post("/api/auth/google", json={"credential": "fake-token"})
        assert r.status_code == 200

        db_user = db_session.execute(select(User).where(User.email == "existing@test.com")).scalar_one()
        assert db_user.google_sub == "google-sub-2"

    def test_google_login_invalid_credential_is_401(self, client, monkeypatch):
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "test-client-id")

        def fake_verify(_credential, _request, _audience):
            raise ValueError("invalid token")

        monkeypatch.setattr(auth_service.id_token, "verify_oauth2_token", fake_verify)

        r = client.post("/api/auth/google", json={"credential": "bad-token"})
        assert r.status_code == 401

    def test_google_login_not_configured_is_503(self, client, monkeypatch):
        monkeypatch.setattr(auth_router, "GOOGLE_CLIENT_ID", "")
        r = client.post("/api/auth/google", json={"credential": "any"})
        assert r.status_code == 503
