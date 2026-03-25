from datetime import date

import pytest
from sqlalchemy import select

from app.models import ReviewState
from app.schemas.learn import MarkStudiedIn, PreferencesIn
from app.services import learn_service
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

    def test_mark_items_studied_transitions_to_reviewing(self, db_session):
        user = make_user(db_session, email="svc-learn-mark@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="mark-studied")
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        make_review_state(db_session, user, prompt, status="learning")

        service_output = learn_service.mark_items_studied(
            db_session,
            user,
            MarkStudiedIn(local_date=date.today().isoformat()),
        )
        assert service_output["marked"] == 1

        state = db_session.execute(
            select(ReviewState).where(
                ReviewState.user_id == user.id,
                ReviewState.prompt_id == prompt.id,
            )
        ).scalar_one()
        assert state.status == "reviewing"

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
