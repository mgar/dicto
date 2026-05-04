"""Development-only sample data for the default test user."""
from datetime import date, datetime, time, timedelta
from itertools import cycle
import os

from sqlalchemy import and_, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import DATABASE_URL, DEFAULT_USER_EMAIL
from app.dependencies import now_utc
from app.db import SessionLocal
from app.models import GrammarPoint, Prompt, ReviewLog, ReviewState, User, VocabItem
from app.services.bootstrap import ensure_default_users
from app.services.seed_service import seed_content
from app.timezone_utils import local_date_from_utc, local_datetime_to_utc_naive


DEV_SAMPLE_DATA_FLAG = "DICTO_DEV_SAMPLE_DATA"
DEV_SAMPLE_TIME_ZONE = "DICTO_DEV_SAMPLE_TIME_ZONE"
LOCAL_DB_HOSTS = {"db", "localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _env_enabled(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _assert_dev_environment() -> None:
    if not _env_enabled(DEV_SAMPLE_DATA_FLAG):
        raise RuntimeError(
            f"{DEV_SAMPLE_DATA_FLAG}=1 is required to load development sample data."
        )

    database_url = make_url(DATABASE_URL)
    if database_url.drivername.startswith("sqlite"):
        return

    if database_url.host not in LOCAL_DB_HOSTS:
        raise RuntimeError(
            "Refusing to load development sample data into a non-local database "
            f"host: {database_url.host!r}."
        )


def _today_in_sample_zone(now: datetime, time_zone: str) -> date:
    return local_date_from_utc(now, time_zone=time_zone)


def _sample_due_at(local_today: date, day_offset: int, time_zone: str, hour: int = 9) -> datetime:
    return local_datetime_to_utc_naive(
        local_today + timedelta(days=day_offset),
        time(hour, 0),
        time_zone=time_zone,
    )


def _prompt_answer(prompt: Prompt) -> str:
    if prompt.answers:
        return prompt.answers[0].answer
    return "sample"


def _load_sample_prompts(db_session: Session, limit_per_kind: int = 36) -> list[Prompt]:
    grammar_prompts = db_session.execute(
        select(Prompt)
        .join(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .where(and_(Prompt.kind == "grammar", GrammarPoint.level.in_(["A1", "A2", "B1"])))
        .order_by(GrammarPoint.level.asc(), GrammarPoint.id.asc(), Prompt.id.asc())
        .limit(limit_per_kind)
    ).scalars().all()
    vocab_prompts = db_session.execute(
        select(Prompt)
        .join(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .where(and_(Prompt.kind == "vocab", VocabItem.level.in_(["A1", "A2", "B1"])))
        .order_by(VocabItem.level.asc(), VocabItem.id.asc(), Prompt.id.asc())
        .limit(limit_per_kind)
    ).scalars().all()
    prompts = []
    for pair in zip(grammar_prompts, vocab_prompts):
        prompts.extend(pair)
    prompts.extend(grammar_prompts[len(vocab_prompts):])
    prompts.extend(vocab_prompts[len(grammar_prompts):])
    return prompts


def _reset_test_user_sample_data(db_session: Session, user: User) -> None:
    db_session.execute(delete(ReviewLog).where(ReviewLog.user_id == user.id))
    db_session.execute(delete(ReviewState).where(ReviewState.user_id == user.id))
    db_session.commit()


def _add_review_states(
    db_session: Session,
    user: User,
    prompts: list[Prompt],
    local_today: date,
    time_zone: str,
) -> int:
    now = now_utc().replace(tzinfo=None)
    state_blueprints = [
        # Pending reviews.
        ("reviewing", -2, 1, 1, 2.30, 8),
        ("reviewing", -1, 3, 2, 2.45, 8),
        ("reviewing", 0, 7, 3, 2.55, 8),
        # Learning queue, which feeds projected reviews.
        ("learning", 0, 0, 0, 2.50, 8),
        # Real scheduled forecast items.
        ("reviewing", 1, 1, 1, 2.35, 6),
        ("reviewing", 2, 6, 2, 2.50, 6),
        ("reviewing", 3, 14, 3, 2.65, 6),
        ("reviewing", 5, 30, 4, 2.80, 6),
        ("reviewing", 8, 75, 5, 2.95, 6),
        ("reviewing", 12, 120, 6, 3.05, 6),
    ]
    prompt_index = 0
    states_added = 0

    for status, day_offset, interval_days, repetitions, ease_factor, count in state_blueprints:
        for _ in range(count):
            if prompt_index >= len(prompts):
                return states_added
            introduced_date = local_today - timedelta(days=max(interval_days, 1))
            if status == "learning":
                introduced_date = local_today
            due_at = (
                now - timedelta(hours=2 + (prompt_index % 6))
                if status == "reviewing" and day_offset <= 0
                else _sample_due_at(local_today, day_offset, time_zone)
            )
            state = ReviewState(
                user_id=user.id,
                prompt_id=prompts[prompt_index].id,
                status=status,
                due_at=due_at,
                interval_days=interval_days,
                repetitions=repetitions,
                ease_factor=ease_factor,
                introduced_at=now - timedelta(days=max(interval_days, 1)),
                introduced_local_date=introduced_date,
                last_reviewed_at=now - timedelta(days=max(day_offset + interval_days, 1))
                if status == "reviewing"
                else None,
            )
            db_session.add(state)
            prompt_index += 1
            states_added += 1

    return states_added


def _add_review_logs(
    db_session: Session,
    user: User,
    prompts: list[Prompt],
    local_today: date,
    time_zone: str,
) -> int:
    if not prompts:
        return 0

    prompt_cycle = cycle(prompts)
    logs_added = 0
    daily_counts = [5, 9, 4, 12, 7, 0, 11, 6, 15, 8, 3, 10, 14, 6]

    for day_index, count in enumerate(daily_counts):
        local_day = local_today - timedelta(days=len(daily_counts) - 1 - day_index)
        for review_index in range(count):
            prompt = next(prompt_cycle)
            is_correct = review_index % 5 != 0
            grade = 4 if is_correct else 2
            answered_at = local_datetime_to_utc_naive(
                local_day,
                time(8 + (review_index % 10), (review_index * 7) % 60),
                time_zone=time_zone,
            )
            db_session.add(
                ReviewLog(
                    user_id=user.id,
                    prompt_id=prompt.id,
                    answered_at=answered_at,
                    local_date=local_day,
                    user_answer=_prompt_answer(prompt) if is_correct else "sample miss",
                    grade=grade,
                    is_correct=is_correct,
                    missing_accent=False,
                    spacing_normalized=False,
                    expected_answer=_prompt_answer(prompt),
                )
            )
            logs_added += 1

    return logs_added


def load_dev_sample_data() -> dict:
    """Load deterministic dashboard/review sample data for the default test user."""
    _assert_dev_environment()
    ensure_default_users()
    seed_content()

    time_zone = os.getenv(DEV_SAMPLE_TIME_ZONE, "America/Los_Angeles")
    db_session = SessionLocal()
    try:
        user = db_session.execute(
            select(User).where(User.email == DEFAULT_USER_EMAIL)
        ).scalar_one()
        user.daily_new_limit = 6
        user.content_preference = "both"
        user.selected_levels = "A1,A2,B1"
        user.last_items_added_at = now_utc().replace(tzinfo=None)
        db_session.commit()

        _reset_test_user_sample_data(db_session, user)

        prompts = _load_sample_prompts(db_session)
        if len(prompts) < 20:
            raise RuntimeError(
                "Not enough seeded prompts to load development sample data. "
                "Run make seed and try again."
            )

        now = now_utc()
        local_today = _today_in_sample_zone(now, time_zone)
        states_added = _add_review_states(db_session, user, prompts, local_today, time_zone)
        logs_added = _add_review_logs(db_session, user, prompts, local_today, time_zone)
        db_session.commit()

        due_now = db_session.execute(
            select(ReviewState)
            .where(
                and_(
                    ReviewState.user_id == user.id,
                    ReviewState.status == "reviewing",
                    ReviewState.due_at <= now_utc().replace(tzinfo=None),
                )
            )
        ).scalars().all()

        return {
            "user_email": user.email,
            "time_zone": time_zone,
            "review_states": states_added,
            "review_logs": logs_added,
            "pending_reviews": len(due_now),
        }
    finally:
        db_session.close()
