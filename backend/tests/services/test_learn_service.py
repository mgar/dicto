from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import ReviewState
from app.dependencies import now_utc
from app.schemas.learn import PreferencesIn
from app.services import learn_service, reviews_service
from app.services.errors import ServiceError
from tests.conftest import make_grammar_point, make_prompt, make_user, make_vocab_item
from tests.services.helpers import make_review_state


class TestLearnService:
    def test_learn_next_validates_count(self, db_session):
        user = make_user(db_session, email="svc-learn-validate@dicto.es", password="pw")
        with pytest.raises(ServiceError):
            learn_service.learn_next(db_session, user, 0, None)
        with pytest.raises(ServiceError):
            learn_service.learn_next(db_session, user, 51, None)

    def test_learn_next_adds_states_and_remaining(self, db_session):
        user = make_user(db_session, email="svc-learn-next@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="learn-next")
        make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ aquí.", answers=("está",))
        make_prompt(db_session, grammar_point=grammar_point, sentence="Yo ___ listo.", answers=("estoy",))

        service_output = learn_service.learn_next(db_session, user, 1, "grammar")
        assert len(service_output["added"]) == 1
        assert service_output["remaining"] == 1

    def test_mark_items_studied_transitions_to_reviewing(self, db_session, monkeypatch):
        user = make_user(db_session, email="svc-learn-mark@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="mark-studied")
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        make_review_state(db_session, user, prompt, status="learning")
        fixed_now = datetime(2026, 4, 29, 15, 30, tzinfo=UTC)
        monkeypatch.setattr(learn_service, "now_utc", lambda: fixed_now)

        service_output = learn_service.mark_items_studied(db_session, user)
        assert service_output["marked"] == 1

        state = db_session.execute(
            select(ReviewState).where(
                ReviewState.user_id == user.id,
                ReviewState.prompt_id == prompt.id,
            )
        ).scalar_one()
        assert state.status == "reviewing"
        assert state.due_at == fixed_now.replace(tzinfo=None) - timedelta(seconds=1)

    def test_mark_items_studied_are_immediately_visible_to_review_queue(self, db_session, monkeypatch):
        user = make_user(db_session, email="svc-learn-mark-visible@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="mark-visible")
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        make_review_state(db_session, user, prompt, status="learning")
        fixed_now = datetime(2026, 4, 29, 15, 30, tzinfo=UTC)
        monkeypatch.setattr(learn_service, "now_utc", lambda: fixed_now)
        monkeypatch.setattr(reviews_service, "now_utc", lambda: fixed_now - timedelta(milliseconds=500))

        learn_service.mark_items_studied(db_session, user)

        assert reviews_service.reviews_count_due(db_session, user)["due_now"] == 1
        queue_output = reviews_service.get_review_queue(db_session, user, limit=10, kind=None)
        assert [item["prompt_id"] for item in queue_output["items"]] == [prompt.id]

    def test_learn_count_matches_unique_study_items(self, db_session):
        user = make_user(db_session, email="svc-learn-count-items@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="count-items-gp")
        make_review_state(
            db_session,
            user,
            make_prompt(
                db_session,
                grammar_point=grammar_point,
                sentence="Count one ___.",
                answers=("es",),
            ),
            status="learning",
        )
        make_review_state(
            db_session,
            user,
            make_prompt(
                db_session,
                grammar_point=grammar_point,
                sentence="Count two ___.",
                answers=("es",),
            ),
            status="learning",
        )
        vocab = make_vocab_item(db_session, level="A1", word="conteo")
        make_review_state(
            db_session,
            user,
            make_prompt(
                db_session,
                kind="vocab",
                vocab_item=vocab,
                sentence="Un ___.",
                answers=("conteo",),
            ),
            status="learning",
        )

        assert learn_service.learn_count(db_session, user, None)["remaining"] == 2
        assert learn_service.learn_count(db_session, user, "grammar")["remaining"] == 1
        assert learn_service.learn_count(db_session, user, "vocab")["remaining"] == 1
        assert learn_service.learn_queue(db_session, user, 10, None)["new_in_queue"] == 2
        assert len(learn_service.get_study_queue(db_session, user)["items"]) == 2

    def test_add_specific_item_uses_user_local_date(self, db_session, monkeypatch):
        user = make_user(db_session, email="svc-learn-add-local@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="add-local-date")
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        monkeypatch.setattr(
            learn_service,
            "now_utc",
            lambda: datetime(2026, 4, 29, 15, 30, tzinfo=UTC),
        )

        service_output = learn_service.learn_add_grammar_point(
            db_session,
            user,
            grammar_point.id,
            tz_offset=-600,
        )

        assert service_output["added"] == 1
        state = db_session.execute(
            select(ReviewState).where(
                ReviewState.user_id == user.id,
                ReviewState.prompt_id == prompt.id,
            )
        ).scalar_one()
        assert state.introduced_local_date == date(2026, 4, 30)

    def test_save_preferences_validation_and_success(self, db_session):
        user = make_user(db_session, email="svc-pref@dicto.es", password="pw")

        with pytest.raises(ServiceError):
            learn_service.save_preferences(
                db_session,
                user,
                PreferencesIn(daily_new_limit=0, content_preference="both", selected_levels=["A1"]),
            )

        service_output = learn_service.save_preferences(
            db_session,
            user,
            PreferencesIn(daily_new_limit=3, content_preference="both", selected_levels=["A1", "A2"]),
        )
        assert service_output["message"].startswith("Preferences saved")
        assert user.selected_levels == "A1,A2"

    def test_auto_add_items_requires_preferences(self, db_session):
        user = make_user(db_session, email="svc-auto-missing@dicto.es", password="pw")
        with pytest.raises(ServiceError) as exc:
            learn_service.auto_add_items(db_session, user, tz_offset=0)
        assert exc.value.status_code == 400

    def test_auto_add_items_adds_items(self, db_session):
        user = make_user(db_session, email="svc-auto@dicto.es", password="pw")
        user.daily_new_limit = 3
        user.content_preference = "both"
        user.selected_levels = "A1"
        db_session.commit()

        grammar_point = make_grammar_point(db_session, level="A1", slug="auto-gp")
        vocab = make_vocab_item(db_session, level="A1", word="pan")
        make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ alta.", answers=("es",))
        make_prompt(db_session, grammar_point=grammar_point, sentence="Yo ___ feliz.", answers=("estoy",))
        make_prompt(
            db_session,
            kind="vocab",
            sentence="Quiero ___.",
            vocab_item=vocab,
            answers=("pan",),
        )

        service_output = learn_service.auto_add_items(db_session, user, tz_offset=0)
        assert service_output["added"] == 3
        assert user.last_items_added_at is not None
        states = db_session.execute(
            select(ReviewState).where(ReviewState.user_id == user.id)
        ).scalars().all()
        assert all(state.introduced_at is not None for state in states)
        assert {state.introduced_local_date for state in states} == {date.today()}

    def test_add_level_unlocks_level_and_fills_daily_batch(self, db_session):
        user = make_user(db_session, email="svc-add-level@dicto.es", password="pw")
        user.daily_new_limit = 2
        user.content_preference = "both"
        user.selected_levels = "A1"
        db_session.commit()

        grammar_point = make_grammar_point(db_session, level="A2", slug="add-level-gp")
        vocab = make_vocab_item(db_session, level="A2", word="mesa")
        make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ lista.", answers=("está",))
        make_prompt(db_session, grammar_point=grammar_point, sentence="Yo ___ de aquí.", answers=("soy",))
        make_prompt(
            db_session,
            kind="vocab",
            sentence="La ___ es grande.",
            vocab_item=vocab,
            answers=("mesa",),
        )

        service_output = learn_service.learn_add_level(db_session, user, "A2", None, None)

        assert service_output["added"] == 2
        assert service_output["daily_limit"] == 2
        assert service_output["unlocked"] is True
        assert user.selected_levels == "A1,A2"
        assert user.last_items_added_at is not None

        states_count = db_session.execute(
            select(ReviewState).where(ReviewState.user_id == user.id)
        ).scalars().all()
        assert len(states_count) == 2

    def test_add_level_does_not_stack_on_unstudied_items(self, db_session):
        user = make_user(db_session, email="svc-add-level-unstudied@dicto.es", password="pw")
        user.daily_new_limit = 2
        user.content_preference = "both"
        user.selected_levels = "A1"
        db_session.commit()

        existing_gp = make_grammar_point(db_session, level="A1", slug="existing-gp")
        existing_prompt = make_prompt(db_session, grammar_point=existing_gp, sentence="Ella ___ aquí.", answers=("está",))
        make_review_state(db_session, user, existing_prompt, status="learning")

        new_gp = make_grammar_point(db_session, level="A2", slug="new-gp")
        make_prompt(db_session, grammar_point=new_gp, sentence="Yo ___ listo.", answers=("estoy",))
        make_prompt(db_session, grammar_point=new_gp, sentence="Nosotros ___ aquí.", answers=("estamos",))

        service_output = learn_service.learn_add_level(db_session, user, "A2", None, None)

        assert service_output["added"] == 0
        assert service_output["unstudied_count"] == 1
        assert user.selected_levels == "A1,A2"

        states = db_session.execute(
            select(ReviewState).where(ReviewState.user_id == user.id)
        ).scalars().all()
        assert len(states) == 1

    def test_add_level_does_not_add_second_daily_batch(self, db_session):
        user = make_user(db_session, email="svc-add-level-today@dicto.es", password="pw")
        user.daily_new_limit = 2
        user.content_preference = "both"
        user.selected_levels = "A1"
        user.last_items_added_at = now_utc().replace(tzinfo=None) - timedelta(minutes=5)
        db_session.commit()

        grammar_point = make_grammar_point(db_session, level="A2", slug="today-gp")
        make_prompt(db_session, grammar_point=grammar_point, sentence="Ella ___ lista.", answers=("está",))

        service_output = learn_service.learn_add_level(db_session, user, "A2", None, None, tz_offset=0)

        assert service_output["added"] == 0
        assert service_output["already_added_today"] is True
        assert user.selected_levels == "A1,A2"

    def test_auto_add_does_not_refill_after_today_items_are_reviewed(self, db_session):
        user = make_user(db_session, email="svc-auto-reviewed-today@dicto.es", password="pw")
        user.daily_new_limit = 2
        user.content_preference = "both"
        user.selected_levels = "A1"
        user.last_items_added_at = now_utc().replace(tzinfo=None) - timedelta(minutes=30)
        db_session.commit()

        answered_at = now_utc().replace(tzinfo=None) - timedelta(minutes=5)
        for idx in range(2):
            grammar_point = make_grammar_point(db_session, level="A1", slug=f"reviewed-today-gp-{idx}")
            prompt = make_prompt(
                db_session,
                grammar_point=grammar_point,
                sentence=f"Reviewed {idx} ___.",
                answers=("es",),
            )
            make_review_state(
                db_session,
                user,
                prompt,
                status="reviewing",
                due_at=answered_at + timedelta(days=1),
                interval_days=1,
                repetitions=1,
                introduced_at=answered_at - timedelta(minutes=25),
                introduced_local_date=date.today(),
            )
            state = db_session.execute(
                select(ReviewState).where(
                    ReviewState.user_id == user.id,
                    ReviewState.prompt_id == prompt.id,
                )
            ).scalar_one()
            state.last_reviewed_at = answered_at

        extra_gp = make_grammar_point(db_session, level="A1", slug="extra-after-review-gp")
        make_prompt(db_session, grammar_point=extra_gp, sentence="Extra ___.", answers=("es",))
        db_session.commit()

        service_output = learn_service.auto_add_items(db_session, user, tz_offset=0)

        assert service_output["added"] == 0
        assert service_output["introduced_today"] == 2
        assert service_output["already_added_today"] is True

    def test_add_level_fills_remaining_daily_allowance_after_limit_increase(self, db_session):
        user = make_user(db_session, email="svc-add-level-increase@dicto.es", password="pw")
        user.daily_new_limit = 5
        user.content_preference = "both"
        user.selected_levels = "A1"
        user.last_items_added_at = now_utc().replace(tzinfo=None) - timedelta(minutes=5)
        db_session.commit()

        answered_at = now_utc().replace(tzinfo=None) - timedelta(minutes=5)
        for idx in range(3):
            grammar_point = make_grammar_point(db_session, level="A1", slug=f"studied-gp-{idx}")
            prompt = make_prompt(
                db_session,
                grammar_point=grammar_point,
                sentence=f"Studied {idx} ___.",
                answers=("es",),
            )
            make_review_state(
                db_session,
                user,
                prompt,
                status="reviewing",
                due_at=answered_at + timedelta(days=1),
                interval_days=1,
                repetitions=1,
                introduced_at=answered_at - timedelta(minutes=25),
                introduced_local_date=date.today(),
            )
            state = db_session.execute(
                select(ReviewState).where(
                    ReviewState.user_id == user.id,
                    ReviewState.prompt_id == prompt.id,
                )
            ).scalar_one()
            state.last_reviewed_at = answered_at

        new_gp = make_grammar_point(db_session, level="A2", slug="increased-limit-gp")
        make_prompt(db_session, grammar_point=new_gp, sentence="Ella ___ lista.", answers=("está",))
        make_prompt(db_session, grammar_point=new_gp, sentence="Yo ___ de aquí.", answers=("soy",))
        make_prompt(db_session, grammar_point=new_gp, sentence="Nosotros ___ aquí.", answers=("estamos",))

        service_output = learn_service.learn_add_level(db_session, user, "A2", None, 5, tz_offset=0)

        assert service_output["added"] == 2
        assert service_output["introduced_today"] == 5
        assert service_output["daily_limit"] == 5
        assert user.selected_levels == "A1,A2"

        states = db_session.execute(
            select(ReviewState).where(ReviewState.user_id == user.id)
        ).scalars().all()
        assert len(states) == 5

    def test_add_level_requires_daily_limit(self, db_session):
        user = make_user(db_session, email="svc-add-level-no-limit@dicto.es", password="pw")

        with pytest.raises(ServiceError) as exc:
            learn_service.learn_add_level(db_session, user, "A1", None, None)

        assert exc.value.status_code == 400

    def test_remove_level_unlock_and_learning_items_only(self, db_session):
        user = make_user(db_session, email="svc-remove-level@dicto.es", password="pw")
        user.daily_new_limit = 3
        user.content_preference = "both"
        user.selected_levels = "A1,A2"
        db_session.commit()

        a2_learning_gp = make_grammar_point(db_session, level="A2", slug="remove-learning")
        a2_reviewing_gp = make_grammar_point(db_session, level="A2", slug="keep-reviewing")
        a1_learning_gp = make_grammar_point(db_session, level="A1", slug="keep-a1")
        a2_learning_prompt = make_prompt(db_session, grammar_point=a2_learning_gp, sentence="A2 learning ___.")
        a2_reviewing_prompt = make_prompt(db_session, grammar_point=a2_reviewing_gp, sentence="A2 reviewing ___.")
        a1_learning_prompt = make_prompt(db_session, grammar_point=a1_learning_gp, sentence="A1 learning ___.")
        make_review_state(db_session, user, a2_learning_prompt, status="learning")
        make_review_state(db_session, user, a2_reviewing_prompt, status="reviewing")
        make_review_state(db_session, user, a1_learning_prompt, status="learning")

        service_output = learn_service.learn_remove_level(db_session, user, "A2")

        assert service_output["selected_levels"] == ["A1"]
        assert service_output["removed_learning_items"] == 1
        assert user.selected_levels == "A1"

        remaining_states = db_session.execute(
            select(ReviewState.prompt_id).where(ReviewState.user_id == user.id)
        ).scalars().all()
        assert set(remaining_states) == {a2_reviewing_prompt.id, a1_learning_prompt.id}
