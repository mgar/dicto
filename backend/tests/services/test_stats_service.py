from datetime import UTC, date, datetime

import pytest

from app.models import ReviewLog
from app.services import stats_service
from app.services.errors import ServiceError
from tests.conftest import make_grammar_point, make_prompt, make_user, make_vocab_item
from tests.services.helpers import make_review_state


class TestStatsService:
    def test_stats_mastery_overview_invalid_kind(self, db_session):
        user = make_user(db_session, email="svc-stats-invalid@dicto.es", password="pw")
        with pytest.raises(ServiceError) as exc:
            stats_service.stats_mastery_overview(db_session, user, "other")
        assert exc.value.status_code == 400

    def test_stats_mastery_overview_returns_tiers(self, db_session):
        user = make_user(db_session, email="svc-stats@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="stats-gp")
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        make_review_state(db_session, user, prompt, interval_days=10)

        service_output = stats_service.stats_mastery_overview(db_session, user, "grammar")
        assert service_output["kind"] == "grammar"
        assert service_output["total_items"] == 1
        assert len(service_output["tiers"]) == 5

    def test_stats_forecast_and_activity_validate_ranges(self, db_session):
        user = make_user(db_session, email="svc-stats-ranges@dicto.es", password="pw")
        with pytest.raises(ServiceError):
            stats_service.stats_forecast(db_session, user, days=0, start_date=None, tz_offset=0)
        with pytest.raises(ServiceError):
            stats_service.stats_activity(db_session, user, days=0, end_date=None)

    def test_stats_activity_returns_daily_series(self, db_session):
        user = make_user(db_session, email="svc-stats-activity@dicto.es", password="pw")
        vocab = make_vocab_item(db_session, level="A1", word="leche")
        prompt = make_prompt(
            db_session,
            kind="vocab",
            sentence="Bebo ___.",
            vocab_item=vocab,
            answers=("leche",),
        )
        db_session.add(
            ReviewLog(
                user_id=user.id,
                prompt_id=prompt.id,
                answered_at=datetime.now(UTC).replace(tzinfo=None),
                local_date=date.today(),
                user_answer="leche",
                grade=4,
                is_correct=True,
                missing_accent=False,
                spacing_normalized=False,
                expected_answer="leche",
            )
        )
        db_session.commit()

        service_output = stats_service.stats_activity(
            db_session,
            user,
            days=3,
            end_date=date.today().isoformat(),
        )
        assert len(service_output["items"]) == 3
        assert service_output["items"][-1]["reviews"] == 1
