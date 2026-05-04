from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.models import ReviewLog
from app.services import reviews_service
from app.services.errors import ServiceError
from tests.conftest import make_grammar_point, make_prompt, make_user
from tests.services.helpers import make_review_state


class TestReviewsService:
    def test_reviews_count_and_queue(self, db_session):
        user = make_user(db_session, email="svc-reviews@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="reviews-gp")
        due_prompt = make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ aquí.", answers=("está",))
        future_prompt = make_prompt(db_session, grammar_point=grammar_point, sentence="Yo ___ listo.", answers=("estoy",))
        make_review_state(
            db_session,
            user,
            due_prompt,
            due_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10),
        )
        make_review_state(
            db_session,
            user,
            future_prompt,
            due_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1),
        )

        count_output = reviews_service.reviews_count_due(db_session, user)
        assert count_output["due_now"] == 1

        queue_output = reviews_service.get_review_queue(db_session, user, limit=10, kind="grammar")
        assert len(queue_output["items"]) == 1
        assert queue_output["items"][0]["prompt_id"] == due_prompt.id

    def test_submit_review_answer_updates_state_and_logs(self, db_session):
        user = make_user(db_session, email="svc-submit@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="submit-gp")
        prompt = make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ de Madrid.", answers=("es",))
        state = make_review_state(
            db_session,
            user,
            prompt,
            due_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=2),
        )

        service_output = reviews_service.submit_review_answer(
            db_session,
            user,
            prompt.id,
            "es",
            local_date=date.today().isoformat(),
            tz_offset=0,
        )
        assert service_output["correct"] is True
        assert service_output["grade"] == 4

        db_session.refresh(state)
        assert state.last_reviewed_at is not None

        log_count = db_session.execute(
            select(func.count()).select_from(ReviewLog).where(ReviewLog.user_id == user.id)
        ).scalar_one()
        assert log_count == 1

    def test_submit_review_answer_missing_accent_uses_weaker_grade(self, db_session):
        user = make_user(db_session, email="svc-submit-accent@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="submit-accent-gp")
        prompt = make_prompt(
            db_session,
            grammar_point=grammar_point,
            sentence="Ella ___ aquí.",
            answers=("está", "esta"),
        )
        make_review_state(
            db_session,
            user,
            prompt,
            due_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=2),
        )

        service_output = reviews_service.submit_review_answer(
            db_session,
            user,
            prompt.id,
            "esta",
            local_date=date.today().isoformat(),
            tz_offset=0,
        )

        assert service_output["correct"] is True
        assert service_output["grade"] == 3
        assert service_output["flags"]["missing_accent"] is True
        assert service_output["expected_answer"] == "está"

        log = db_session.execute(
            select(ReviewLog).where(ReviewLog.user_id == user.id)
        ).scalar_one()
        assert log.is_correct is True
        assert log.grade == 3
        assert log.missing_accent is True

    def test_submit_review_answer_uses_time_zone_for_dst(self, db_session, monkeypatch):
        user = make_user(db_session, email="svc-submit-dst@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="submit-dst-gp")
        prompt = make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ de Madrid.", answers=("es",))
        state = make_review_state(
            db_session,
            user,
            prompt,
            due_at=datetime(2026, 3, 7, 18, 0),
            interval_days=0,
            repetitions=0,
        )
        monkeypatch.setattr(
            reviews_service,
            "now_utc",
            lambda: datetime(2026, 3, 7, 18, 0, tzinfo=UTC),
        )

        reviews_service.submit_review_answer(
            db_session,
            user,
            prompt.id,
            "es",
            local_date="2026-03-07",
            tz_offset=480,
            time_zone="America/Los_Angeles",
        )

        db_session.refresh(state)
        assert state.due_at == datetime(2026, 3, 8, 11, 0)

    def test_submit_review_answer_requires_state(self, db_session):
        user = make_user(db_session, email="svc-submit-missing@dicto.es", password="pw")
        with pytest.raises(ServiceError) as exc:
            reviews_service.submit_review_answer(db_session, user, 9999, "x", None, None)
        assert exc.value.status_code == 404
