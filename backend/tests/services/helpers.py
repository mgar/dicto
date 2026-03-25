from datetime import UTC, datetime

from app.models import ReviewState


def make_review_state(
    db_session,
    user,
    prompt,
    *,
    status="reviewing",
    due_at=None,
    interval_days=3,
    repetitions=2,
    ease_factor=2.5,
):
    state = ReviewState(
        user_id=user.id,
        prompt_id=prompt.id,
        status=status,
        due_at=due_at or datetime.now(UTC).replace(tzinfo=None),
        interval_days=interval_days,
        repetitions=repetitions,
        ease_factor=ease_factor,
    )
    db_session.add(state)
    db_session.commit()
    return state