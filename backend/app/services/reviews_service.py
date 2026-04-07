"""Review queue and answer submission."""
from datetime import datetime, time, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import GrammarPoint, Prompt, PromptAnswer, ReviewLog, ReviewState, User, VocabItem
from app.services.errors import ServiceError
from app.utils import grade_cloze, prompt_to_dict, sm2_update


def reviews_count_due(db_session: Session, user: User) -> dict:
    due_now = now_utc().replace(tzinfo=None)
    stmt = select(func.count()).select_from(ReviewState).where(
        and_(
            ReviewState.user_id == user.id,
            ReviewState.status == "reviewing",
            ReviewState.due_at <= due_now,
        )
    )
    due_now_count = int(db_session.execute(stmt).scalar_one())
    return {"due_now": due_now_count}


def get_review_queue(db_session: Session, user: User, limit: int, kind: str | None) -> dict:
    due_now = now_utc().replace(tzinfo=None)
    stmt = (
        select(ReviewState, Prompt, GrammarPoint, VocabItem)
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "reviewing",
                ReviewState.due_at <= due_now,
            )
        )
    )
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    stmt = stmt.order_by(ReviewState.due_at.asc()).limit(limit)

    rows = db_session.execute(stmt).all()
    items = []
    for review_state, prompt, grammar_point, vocab_item in rows:
        item = prompt_to_dict(prompt, grammar_point, vocab_item)
        item["due_at"] = review_state.due_at.isoformat()
        items.append(item)
    return {"items": items}


def submit_review_answer(
    db_session: Session,
    user: User,
    prompt_id: int,
    user_answer: str,
    local_date: str | None,
    tz_offset: int | None,
) -> dict:
    review_state = db_session.execute(
        select(ReviewState).where(and_(ReviewState.user_id == user.id, ReviewState.prompt_id == prompt_id))
    ).scalar_one_or_none()
    if not review_state:
        raise ServiceError(404, "No review state for this prompt")

    prompt_rows = db_session.execute(
        select(Prompt, PromptAnswer)
        .outerjoin(PromptAnswer, PromptAnswer.prompt_id == Prompt.id)
        .where(Prompt.id == prompt_id)
    ).all()
    if not prompt_rows:
        raise ServiceError(404, "Prompt not found")
    prompt = prompt_rows[0][0]
    accepted = [row[1].answer for row in prompt_rows if row[1] is not None]

    is_correct, grade, flags, expected = grade_cloze(user_answer, accepted)

    new_ease_factor, interval, new_repetitions = sm2_update(
        ease_factor=float(review_state.ease_factor),
        interval_days=int(review_state.interval_days),
        repetitions=int(review_state.repetitions),
        grade=int(grade),
    )

    answered_at = now_utc().replace(tzinfo=None)

    if local_date:
        try:
            local_today = datetime.fromisoformat(local_date).date()
        except ValueError:
            local_today = answered_at.date()
    else:
        local_today = answered_at.date()

    offset_minutes = -(tz_offset or 0)
    due_date = local_today + timedelta(days=interval)
    local_4am_utc = datetime.combine(due_date, time(4, 0, 0)) - timedelta(minutes=offset_minutes)
    due_at = local_4am_utc

    min_due = answered_at + timedelta(hours=1)
    if due_at < min_due:
        due_at = min_due

    review_state.ease_factor = new_ease_factor
    review_state.interval_days = interval
    review_state.repetitions = new_repetitions
    review_state.last_reviewed_at = answered_at
    review_state.due_at = due_at

    log = ReviewLog(
        user_id=user.id,
        prompt_id=prompt_id,
        answered_at=answered_at,
        local_date=local_today,
        user_answer=user_answer,
        grade=grade,
        is_correct=is_correct,
        missing_accent=bool(flags.get("missing_accent", False)),
        spacing_normalized=bool(flags.get("spacing_normalized", False)),
        expected_answer=expected,
    )
    db_session.add(log)
    db_session.commit()

    return {
        "correct": is_correct,
        "grade": grade,
        "flags": flags,
        "expected_answer": expected,
        "next_due_at": due_at.isoformat(),
    }
