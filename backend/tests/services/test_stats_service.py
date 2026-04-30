from datetime import UTC, date, datetime, timedelta

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

    def test_stats_forecast_returns_scheduled_reviews(self, db_session):
        user = make_user(db_session, email="svc-stats-forecast@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="forecast-gp")
        grammar_prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        vocab = make_vocab_item(db_session, level="A1", word="agua")
        vocab_prompt = make_prompt(
            db_session,
            kind="vocab",
            sentence="Bebo ___.",
            vocab_item=vocab,
            answers=("agua",),
        )
        start_day = date(2026, 4, 29)

        make_review_state(
            db_session,
            user,
            grammar_prompt,
            due_at=datetime.combine(start_day - timedelta(days=1), datetime.min.time()),
        )
        make_review_state(
            db_session,
            user,
            vocab_prompt,
            due_at=datetime.combine(start_day + timedelta(days=2), datetime.min.time()),
        )

        service_output = stats_service.stats_forecast(
            db_session,
            user,
            days=4,
            start_date=start_day.isoformat(),
            tz_offset=0,
        )

        assert service_output["items"][0]["due"] == 1
        assert service_output["items"][0]["grammar_due"] == 1
        assert service_output["items"][2]["due"] == 1
        assert service_output["items"][2]["vocab_due"] == 1

    def test_stats_forecast_projects_future_daily_batches(self, db_session):
        user = make_user(db_session, email="svc-stats-projected@dicto.es", password="pw")
        user.daily_new_limit = 3
        user.content_preference = "both"
        user.selected_levels = "A1"

        for idx in range(2):
            grammar_point = make_grammar_point(
                db_session,
                level="A1",
                slug=f"project-gp-{idx}",
            )
            make_prompt(db_session, grammar_point=grammar_point, answers=("es",))

        for idx in range(2):
            vocab = make_vocab_item(db_session, level="A1", word=f"palabra-{idx}")
            make_prompt(
                db_session,
                kind="vocab",
                sentence=f"Uso ___ {idx}.",
                vocab_item=vocab,
                answers=(f"palabra-{idx}",),
            )

        db_session.commit()
        service_output = stats_service.stats_forecast(
            db_session,
            user,
            days=8,
            start_date=date(2026, 4, 29).isoformat(),
            tz_offset=0,
        )

        assert service_output["items"][0]["projected_due"] == 3
        assert service_output["items"][0]["projected_grammar_due"] == 2
        assert service_output["items"][0]["projected_vocab_due"] == 1
        assert service_output["items"][1]["projected_due"] == 4
        assert service_output["items"][1]["projected_vocab_due"] == 2
        assert service_output["items"][7]["projected_due"] == 3

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
