"""
Shared pytest fixtures: in-memory SQLite DB, TestClient, and helper factories.

The engine uses SQLite so no MySQL is required to run tests.
SQLAlchemy's `check_same_thread=False` is needed for SQLite with FastAPI.
"""
import os
os.environ.setdefault("TESTING", "1")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.dependencies import get_db
from app.main import app
from app.models import User, Session as DbSession, GrammarPoint, VocabItem, Prompt, PromptAnswer
from app.core.security import hash_password
from app.dependencies import now_utc, COOKIE_NAME

import uuid
from datetime import timedelta

SQLALCHEMY_TEST_URL = "sqlite://"


@pytest.fixture(scope="function")
def db_engine():
    # StaticPool ensures all connections share the same in-memory SQLite DB,
    # so tables created by create_all() are visible to every subsequent query.
    engine = create_engine(
        SQLALCHEMY_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with the DB dependency overridden to use the test session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---- User factories ----

def make_user(db_session, email="user@test.com", password="secret", is_admin=False) -> User:
    u = User(
        email=email,
        password_hash=hash_password(password),
        display_name="Test User",
        is_admin=is_admin,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def make_session(db_session, user: User, expired=False) -> str:
    """Create a DB session and return the session ID (to use as cookie)."""
    session_id = str(uuid.uuid4())
    delta = timedelta(days=-1) if expired else timedelta(days=14)
    expires_at = (now_utc() + delta).replace(tzinfo=None)
    s = DbSession(id=session_id, user_id=user.id, expires_at=expires_at)
    db_session.add(s)
    db_session.commit()
    return session_id
