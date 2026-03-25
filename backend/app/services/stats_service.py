"""Statistics: mastery, forecast, activity."""
from datetime import datetime, time, timedelta

from sqlalchemy import and_, case, func, literal_column, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import GrammarPoint, Prompt, ReviewLog, ReviewState, User, VocabItem
from app.services.errors import ServiceError
from app.utils import MASTERY_TIER_LABELS, MASTERY_TIER_ORDER, mastery_key_from_interval


def stats_mastery_overview(db_session: Session, user: User, kind: str) -> dict:
    if kind not in {"grammar", "vocab"}:
        raise ServiceError(400, "kind must be 'grammar' or 'vocab'")

    if kind == "grammar":
        item_model = GrammarPoint
        prompt_fk = Prompt.grammar_point_id
    else:
        item_model = VocabItem
        prompt_fk = Prompt.vocab_item_id

    rows = db_session.execute(
        select(
            item_model.id.label("item_id"),
            func.count(Prompt.id).label("total_prompts"),
            func.sum(case((ReviewState.prompt_id.is_not(None), 1), else_=0)).label("reviewed_prompts"),
            func.avg(func.coalesce(ReviewState.interval_days, 0)).label("avg_interval_days"),
        )
        .join(Prompt, prompt_fk == item_model.id)
        .join(
            ReviewState,
            and_(
                ReviewState.prompt_id == Prompt.id,
                ReviewState.user_id == user.id,
            ),
        )
        .where(Prompt.kind == kind)
        .group_by(item_model.id)
    ).all()

    tier_counts = {tier_key: 0 for tier_key in MASTERY_TIER_ORDER}
    for row in rows:
        key = mastery_key_from_interval(float(row.avg_interval_days or 0.0))
        tier_counts[key] += 1

    return {
        "kind": kind,
        "total_items": len(rows),
        "tiers": [
            {
                "key": key,
                "label": MASTERY_TIER_LABELS[key],
                "count": tier_counts[key],
            }
            for key in MASTERY_TIER_ORDER
        ],
    }


def stats_forecast(
    db_session: Session,
    user: User,
    days: int,
    start_date: str | None,
    tz_offset: int | None,
) -> dict:
    if days < 1 or days > 90:
        raise ServiceError(400, "days must be between 1 and 90")

    if start_date:
        try:
            today = datetime.fromisoformat(start_date).date()
        except ValueError:
            today = now_utc().date()
    else:
        today = now_utc().date()

    offset_minutes = -(tz_offset or 0)
    local_due = func.timestampadd(
        literal_column("MINUTE"), offset_minutes, ReviewState.due_at
    )

    start_dt = datetime.combine(today, time.min).replace(tzinfo=None)
    end_dt_exclusive = datetime.combine(today + timedelta(days=days), time.min).replace(tzinfo=None)

    date_expr = case(
        (local_due < start_dt, func.date(start_dt)),
        else_=func.date(local_due),
    )

    stmt = (
        select(
            date_expr.label("d"),
            func.count().label("due"),
            func.sum(case((Prompt.kind == "grammar", 1), else_=0)).label("grammar_due"),
            func.sum(case((Prompt.kind == "vocab", 1), else_=0)).label("vocab_due"),
        )
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "reviewing",
                local_due < end_dt_exclusive,
            )
        )
        .group_by(date_expr)
        .order_by(date_expr.asc())
    )

    rows = db_session.execute(stmt).all()
    counts_by_date = {
        row.d: {
            "due": int(row.due),
            "grammar_due": int(row.grammar_due or 0),
            "vocab_due": int(row.vocab_due or 0),
        }
        for row in rows
    }

    items = []
    for day_offset in range(days):
        calendar_date = today + timedelta(days=day_offset)
        counts = counts_by_date.get(
            calendar_date, {"due": 0, "grammar_due": 0, "vocab_due": 0}
        )
        items.append({"date": calendar_date.isoformat(), **counts})

    return {"items": items}


def stats_activity(db_session: Session, user: User, days: int, end_date: str | None) -> dict:
    if days < 1 or days > 365:
        raise ServiceError(400, "days must be between 1 and 365")

    if end_date:
        try:
            local_today = datetime.fromisoformat(end_date).date()
        except ValueError:
            local_today = now_utc().date()
    else:
        local_today = now_utc().date()

    start_day = local_today - timedelta(days=days - 1)

    correct_case = case((ReviewLog.is_correct == True, 1), else_=0)
    date_col = func.coalesce(ReviewLog.local_date, func.date(ReviewLog.answered_at))

    stmt = (
        select(
            date_col.label("d"),
            func.count().label("reviews"),
            func.sum(correct_case).label("correct"),
            func.sum(case((Prompt.kind == "grammar", 1), else_=0)).label("grammar_reviews"),
            func.sum(case((Prompt.kind == "vocab", 1), else_=0)).label("vocab_reviews"),
        )
        .join(Prompt, Prompt.id == ReviewLog.prompt_id)
        .where(
            and_(
                ReviewLog.user_id == user.id,
                date_col >= start_day,
                date_col <= local_today,
            )
        )
        .group_by(date_col)
        .order_by(date_col.asc())
    )

    rows = db_session.execute(stmt).all()
    stats_by_date = {
        row.d: {
            "reviews": int(row.reviews),
            "correct": int(row.correct or 0),
            "grammar_reviews": int(row.grammar_reviews or 0),
            "vocab_reviews": int(row.vocab_reviews or 0),
        }
        for row in rows
    }

    items = []
    for day_offset in range(days):
        calendar_date = start_day + timedelta(days=day_offset)
        counts = stats_by_date.get(
            calendar_date,
            {"reviews": 0, "correct": 0, "grammar_reviews": 0, "vocab_reviews": 0},
        )
        items.append({"date": calendar_date.isoformat(), **counts})

    return {"items": items}
