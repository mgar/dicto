"""
Fixtures for testing in-memory with SQLite DB, TestClient, and helper factories.

The engine is set to SQLite so no MySQL is required to run tests.

SQLAlchemy's `check_same_thread=False` is needed for SQLite with FastAPI.

See: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#test-applications-with-fastapi-and-sqlmodel
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

def make_user(db_session, email="user@dicto.es", password="secret", is_admin=False) -> User:
    user_record = User(
        email=email,
        password_hash=hash_password(password),
        display_name="Test User",
        is_admin=is_admin,
    )
    db_session.add(user_record)
    db_session.commit()
    db_session.refresh(user_record)
    return user_record


def make_session(db_session, user: User, expired=False) -> str:
    """Create a DB session and return the session ID (to use as cookie)."""
    session_id = str(uuid.uuid4())
    delta = timedelta(days=-1) if expired else timedelta(days=14)
    expires_at = (now_utc() + delta).replace(tzinfo=None)
    session_record = DbSession(id=session_id, user_id=user.id, expires_at=expires_at)
    db_session.add(session_record)
    db_session.commit()
    return session_id


def make_grammar_point(db_session, level="A1", slug="ser-estar", title="Ser vs Estar") -> GrammarPoint:
    grammar_point_record = GrammarPoint(
        level=level,
        slug=slug,
        title=title,
        short_description="To be or to be.",
        explanation="Ser is permanent; estar is temporary.",
    )
    db_session.add(grammar_point_record)
    db_session.commit()
    db_session.refresh(grammar_point_record)
    return grammar_point_record


def make_vocab_item(db_session, word="casa", level="A1") -> VocabItem:
    vocab_item_record = VocabItem(
        level=level,
        word=word,
        translation="house",
        part_of_speech="noun",
        gender="f",
    )
    db_session.add(vocab_item_record)
    db_session.commit()
    db_session.refresh(vocab_item_record)
    return vocab_item_record


def make_prompt(db_session, sentence="Ella ___ de Madrid.", kind="grammar",
                grammar_point=None, vocab_item=None, answers=("es",)) -> Prompt:
    prompt_record = Prompt(
        kind=kind,
        sentence=sentence,
        grammar_point_id=grammar_point.id if grammar_point else None,
        vocab_item_id=vocab_item.id if vocab_item else None,
    )
    db_session.add(prompt_record)
    db_session.flush()
    for accepted_answer in answers:
        db_session.add(PromptAnswer(prompt_id=prompt_record.id, answer=accepted_answer))
    db_session.commit()
    db_session.refresh(prompt_record)
    return prompt_record
