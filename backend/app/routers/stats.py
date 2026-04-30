"""
Statistics routes: forecast, activity.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.services import stats_service
from app.services.errors import ServiceError, raise_http

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/mastery-overview")
def stats_mastery_overview(
    kind: str = "grammar",
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get mastery distribution by item for grammar or vocab."""
    try:
        return stats_service.stats_mastery_overview(db_session, user, kind)
    except ServiceError as err:
        raise_http(err)


@router.get("/forecast")
def stats_forecast(
    days: int = 14,
    start_date: str | None = None,
    tz_offset: int | None = None,
    time_zone: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get forecast of upcoming reviews."""
    try:
        return stats_service.stats_forecast(
            db_session,
            user,
            days,
            start_date,
            tz_offset,
            time_zone,
        )
    except ServiceError as err:
        raise_http(err)


@router.get("/activity")
def stats_activity(
    days: int = 30,
    end_date: str | None = None,
    tz_offset: int | None = None,
    time_zone: str | None = None,
    db_session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get activity history."""
    try:
        return stats_service.stats_activity(
            db_session,
            user,
            days,
            end_date,
            tz_offset,
            time_zone,
        )
    except ServiceError as err:
        raise_http(err)
