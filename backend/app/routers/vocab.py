"""
Vocabulary items routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.services import vocab_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/vocab-items", tags=["vocab"])


@router.get("/by-level")
def list_vocab_items_by_level(
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Returns vocab items grouped by CEFR level, with progress info for the user."""
    return vocab_service.list_vocab_items_by_level(db_session, user)


@router.get("")
def list_vocab_items(
    level: str | None = None,
    tag: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all vocab items with optional filters."""
    return vocab_service.list_vocab_items(db_session, level, tag)


@router.get("/{vocab_item_id}")
def get_vocab_item(
    vocab_item_id: int,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single vocab item."""
    try:
        return vocab_service.get_vocab_item(db_session, user, vocab_item_id)
    except ServiceError as err:
        raise_http(err)
