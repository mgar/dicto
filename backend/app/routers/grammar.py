"""
Grammar points routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.services import grammar_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/grammar-points", tags=["grammar"])


@router.get("")
def list_grammar_points(
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all grammar points."""
    return grammar_service.list_grammar_points(db_session)


@router.get("/by-level")
def list_grammar_points_by_level(
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Returns grammar points grouped by CEFR level, with progress info for the user."""
    return grammar_service.list_grammar_points_by_level(db_session, user)


@router.get("/{grammar_point_id}")
def get_grammar_point(
    grammar_point_id: int,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single grammar point with examples."""
    try:
        return grammar_service.get_grammar_point(db_session, user, grammar_point_id)
    except ServiceError as err:
        raise_http(err)
