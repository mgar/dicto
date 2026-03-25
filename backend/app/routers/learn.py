"""
Learning queue routes.
"""
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import MarkStudiedIn, PreferencesIn
from app.services import learn_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/learn", tags=["learn"])


@router.get("/levels")
def get_learn_levels(
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Returns all CEFR levels with grammar and vocab counts, plus user's queue status."""
    return learn_service.get_learn_levels(db_session, user)


@router.get("/count")
def learn_count(
    kind: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Count items in the user's queue that haven't been reviewed yet."""
    return learn_service.learn_count(db_session, user, kind)


@router.get("/queue")
def learn_queue(
    limit: int = 20,
    kind: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Returns the next prompts that are not yet in review_state for this user."""
    return learn_service.learn_queue(db_session, user, limit, kind)


@router.post("/next")
def learn_next(
    count: int = 5,
    kind: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Adds the next N unseen prompts to review_state with due_at=now."""
    try:
        return learn_service.learn_next(db_session, user, count, kind)
    except ServiceError as err:
        raise_http(err)


@router.post("/add-grammar-point/{grammar_point_id}")
def learn_add_grammar_point(
    grammar_point_id: int,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Adds all prompts from a specific grammar point to the user's learning queue."""
    try:
        return learn_service.learn_add_grammar_point(db_session, user, grammar_point_id)
    except ServiceError as err:
        raise_http(err)


@router.post("/add-vocab-item/{vocab_item_id}")
def learn_add_vocab_item(
    vocab_item_id: int,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Adds all prompts from a specific vocab item to the user's learning queue."""
    try:
        return learn_service.learn_add_vocab_item(db_session, user, vocab_item_id)
    except ServiceError as err:
        raise_http(err)


@router.post("/add-level/{level}")
def learn_add_level(
    level: str,
    kind: str | None = None,
    limit: int | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Adds prompts from a CEFR level to the learning queue."""
    try:
        return learn_service.learn_add_level(db_session, user, level, kind, limit)
    except ServiceError as err:
        raise_http(err)


@router.get("/study-queue")
def get_study_queue(
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get items in the user's queue that haven't been studied yet (status='learning')."""
    return learn_service.get_study_queue(db_session, user)


@router.post("/mark-studied")
def mark_items_studied(
    payload: MarkStudiedIn | None = Body(default=None),
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark all items with status='learning' as ready for review."""
    return learn_service.mark_items_studied(db_session, user, payload)


@router.post("/preferences")
def save_preferences(
    prefs: PreferencesIn,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Save user's learning preferences: daily goal, content type, and levels."""
    try:
        return learn_service.save_preferences(db_session, user, prefs)
    except ServiceError as err:
        raise_http(err)


@router.post("/auto-add")
def auto_add_items(
    tz_offset: int | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Automatically add new items based on user's saved preferences."""
    try:
        return learn_service.auto_add_items(db_session, user, tz_offset)
    except ServiceError as err:
        raise_http(err)
