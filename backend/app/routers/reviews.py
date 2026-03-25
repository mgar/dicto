"""
Review queue and answer submission routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas import SubmitAnswerIn
from app.services import reviews_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/count")
def reviews_count(
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Count reviews due now."""
    return reviews_service.reviews_count_due(db_session, user)


@router.get("/queue")
def get_review_queue(
    limit: int = 20,
    kind: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the review queue with due items."""
    return reviews_service.get_review_queue(db_session, user, limit, kind)


@router.post("/{prompt_id}/answer")
def submit_review_answer(
    prompt_id: int,
    payload: SubmitAnswerIn,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit an answer for a review item."""
    try:
        return reviews_service.submit_review_answer(
            db_session,
            user,
            prompt_id,
            payload.user_answer,
            payload.local_date,
            payload.tz_offset,
        )
    except ServiceError as err:
        raise_http(err)
