"""Statistics: mastery, forecast, activity."""
from datetime import datetime, time, timedelta

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import GrammarPoint, Prompt, ReviewLog, ReviewState, User, VocabItem
from app.services.errors import ServiceError
from app.timezone_utils import local_date_from_utc, local_datetime_to_utc_naive
from app.utils import (
    MASTERY_TIER_LABELS,
    MASTERY_TIER_ORDER,
    mastery_key_from_interval,
    sm2_update,
)


PROJECTED_REVIEW_GRADE = 4


def _selected_levels(user: User) -> list[str]:
    if not user.selected_levels:
        return []
    return [level for level in user.selected_levels.split(",") if level]


def _projected_review_offsets(days: int) -> list[int]:
    offsets = []
    offset = 0
    ease_factor = 2.5
    interval_days = 0
    repetitions = 0

    while offset < days:
        offsets.append(offset)
        ease_factor, interval_days, repetitions = sm2_update(
            ease_factor=ease_factor,
            interval_days=interval_days,
            repetitions=repetitions,
            grade=PROJECTED_REVIEW_GRADE,
        )
        offset += interval_days

    return offsets


def _take_projected_batch(
    available_by_kind: dict[str, int],
    daily_limit: int,
    content_preference: str | None,
) -> dict[str, int]:
    if daily_limit <= 0:
        return {"grammar": 0, "vocab": 0}

    if content_preference in {"grammar", "vocab"}:
        count = min(available_by_kind.get(content_preference, 0), daily_limit)
        available_by_kind[content_preference] = (
            available_by_kind.get(content_preference, 0) - count
        )
        return {
            "grammar": count if content_preference == "grammar" else 0,
            "vocab": count if content_preference == "vocab" else 0,
        }

    grammar_count = min(available_by_kind.get("grammar", 0), (daily_limit + 1) // 2)
    vocab_count = min(available_by_kind.get("vocab", 0), daily_limit - grammar_count)
    remaining = daily_limit - grammar_count - vocab_count

    if remaining > 0:
        extra_grammar = min(
            available_by_kind.get("grammar", 0) - grammar_count,
            remaining,
        )
        grammar_count += extra_grammar
        remaining -= extra_grammar

    if remaining > 0:
        extra_vocab = min(
            available_by_kind.get("vocab", 0) - vocab_count,
            remaining,
        )
        vocab_count += extra_vocab

    available_by_kind["grammar"] = available_by_kind.get("grammar", 0) - grammar_count
    available_by_kind["vocab"] = available_by_kind.get("vocab", 0) - vocab_count
    return {"grammar": grammar_count, "vocab": vocab_count}


def _add_projected_review_wave(
    projected_by_date: dict,
    start_day,
    batch: dict[str, int],
    today,
    days: int,
) -> None:
    if not batch["grammar"] and not batch["vocab"]:
        return

    for review_offset in _projected_review_offsets(days):
        projected_date = start_day + timedelta(days=review_offset)
        day_offset = (projected_date - today).days
        if day_offset < 0 or day_offset >= days:
            continue

        projected_counts = projected_by_date[projected_date]
        projected_counts["projected_grammar_due"] += batch["grammar"]
        projected_counts["projected_vocab_due"] += batch["vocab"]
        projected_counts["projected_due"] += batch["grammar"] + batch["vocab"]


def _projected_reviews_by_date(
    db_session: Session,
    user: User,
    today,
    days: int,
) -> dict:
    projected_by_date = {
        today + timedelta(days=day_offset): {
            "projected_due": 0,
            "projected_grammar_due": 0,
            "projected_vocab_due": 0,
        }
        for day_offset in range(days)
    }

    if not user.daily_new_limit or not user.selected_levels:
        return projected_by_date

    levels = _selected_levels(user)
    available_stmt = (
        select(Prompt.kind, func.count(Prompt.id))
        .select_from(Prompt)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(
            and_(
                ReviewState.prompt_id.is_(None),
                or_(GrammarPoint.level.in_(levels), VocabItem.level.in_(levels)),
            )
        )
        .group_by(Prompt.kind)
    )
    available_by_kind = {
        kind: int(count)
        for kind, count in db_session.execute(available_stmt).all()
    }

    learning_stmt = (
        select(Prompt.kind, func.count(ReviewState.prompt_id))
        .select_from(ReviewState)
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "learning",
            )
        )
        .group_by(Prompt.kind)
    )
    learning_batch = {"grammar": 0, "vocab": 0}
    for kind, count in db_session.execute(learning_stmt).all():
        learning_batch[kind] = int(count)

    learning_total = learning_batch["grammar"] + learning_batch["vocab"]
    _add_projected_review_wave(projected_by_date, today, learning_batch, today, days)

    introduced_today = int(
        db_session.execute(
            select(func.count())
            .select_from(ReviewState)
            .where(
                and_(
                    ReviewState.user_id == user.id,
                    ReviewState.introduced_local_date == today,
                )
            )
        ).scalar_one()
    )

    for day_offset in range(days):
        planned_day = today + timedelta(days=day_offset)
        if day_offset == 0 and learning_total > 0:
            daily_limit = 0
        elif day_offset == 0:
            daily_limit = max(user.daily_new_limit - introduced_today, 0)
        else:
            daily_limit = user.daily_new_limit

        batch = _take_projected_batch(
            available_by_kind,
            daily_limit,
            user.content_preference,
        )
        _add_projected_review_wave(projected_by_date, planned_day, batch, today, days)

    return projected_by_date


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
    time_zone: str | None = None,
) -> dict:
    if days < 1 or days > 90:
        raise ServiceError(400, "days must be between 1 and 90")

    now = now_utc()
    if start_date:
        try:
            today = datetime.fromisoformat(start_date).date()
        except ValueError:
            today = local_date_from_utc(now, tz_offset, time_zone)
    else:
        today = local_date_from_utc(now, tz_offset, time_zone)

    end_utc_exclusive = local_datetime_to_utc_naive(
        today + timedelta(days=days),
        time.min,
        tz_offset,
        time_zone,
    )

    stmt = (
        select(
            ReviewState.due_at,
            Prompt.kind,
        )
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "reviewing",
                ReviewState.due_at < end_utc_exclusive,
            )
        )
        .order_by(ReviewState.due_at.asc())
    )

    rows = db_session.execute(stmt).all()
    counts_by_date = {
        today + timedelta(days=day_offset): {
            "due": 0,
            "grammar_due": 0,
            "vocab_due": 0,
        }
        for day_offset in range(days)
    }
    for due_at, kind in rows:
        local_due_date = local_date_from_utc(due_at, tz_offset, time_zone)
        calendar_date = max(local_due_date, today)
        if calendar_date not in counts_by_date:
            continue
        counts_by_date[calendar_date]["due"] += 1
        if kind == "grammar":
            counts_by_date[calendar_date]["grammar_due"] += 1
        elif kind == "vocab":
            counts_by_date[calendar_date]["vocab_due"] += 1

    projected_by_date = _projected_reviews_by_date(db_session, user, today, days)

    items = []
    for day_offset in range(days):
        calendar_date = today + timedelta(days=day_offset)
        items.append({
            "date": calendar_date.isoformat(),
            **counts_by_date[calendar_date],
            **projected_by_date[calendar_date],
        })

    return {"items": items}


def stats_activity(
    db_session: Session,
    user: User,
    days: int,
    end_date: str | None,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> dict:
    if days < 1 or days > 365:
        raise ServiceError(400, "days must be between 1 and 365")

    now = now_utc()
    if end_date:
        try:
            local_today = datetime.fromisoformat(end_date).date()
        except ValueError:
            local_today = local_date_from_utc(now, tz_offset, time_zone)
    else:
        local_today = local_date_from_utc(now, tz_offset, time_zone)

    start_day = local_today - timedelta(days=days - 1)
    start_utc_inclusive = local_datetime_to_utc_naive(
        start_day,
        time.min,
        tz_offset,
        time_zone,
    )
    end_utc_exclusive = local_datetime_to_utc_naive(
        local_today + timedelta(days=1),
        time.min,
        tz_offset,
        time_zone,
    )

    rows = db_session.execute(
        select(
            ReviewLog.local_date,
            ReviewLog.answered_at,
            ReviewLog.is_correct,
            Prompt.kind,
        )
        .join(Prompt, Prompt.id == ReviewLog.prompt_id)
        .where(
            and_(
                ReviewLog.user_id == user.id,
                or_(
                    and_(
                        ReviewLog.local_date.is_not(None),
                        ReviewLog.local_date >= start_day,
                        ReviewLog.local_date <= local_today,
                    ),
                    and_(
                        ReviewLog.local_date.is_(None),
                        ReviewLog.answered_at >= start_utc_inclusive,
                        ReviewLog.answered_at < end_utc_exclusive,
                    ),
                ),
            )
        )
        .order_by(ReviewLog.answered_at.asc())
    ).all()

    stats_by_date = {
        start_day + timedelta(days=day_offset): {
            "reviews": 0,
            "correct": 0,
            "grammar_reviews": 0,
            "vocab_reviews": 0,
        }
        for day_offset in range(days)
    }
    for local_date, answered_at, is_correct, kind in rows:
        calendar_date = local_date or local_date_from_utc(answered_at, tz_offset, time_zone)
        if calendar_date not in stats_by_date:
            continue
        stats_by_date[calendar_date]["reviews"] += 1
        if is_correct:
            stats_by_date[calendar_date]["correct"] += 1
        if kind == "grammar":
            stats_by_date[calendar_date]["grammar_reviews"] += 1
        elif kind == "vocab":
            stats_by_date[calendar_date]["vocab_reviews"] += 1

    items = []
    for day_offset in range(days):
        calendar_date = start_day + timedelta(days=day_offset)
        items.append({"date": calendar_date.isoformat(), **stats_by_date[calendar_date]})

    return {"items": items}
