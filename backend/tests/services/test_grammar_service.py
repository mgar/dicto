from datetime import UTC, datetime, timedelta

import pytest

from app.services import grammar_service
from app.services.errors import ServiceError
from tests.conftest import make_grammar_point, make_prompt, make_user
from tests.services.helpers import make_review_state


class TestGrammarService:
    def test_list_grammar_points_and_by_level(self, db_session):
        user = make_user(db_session, email="svc-grammar@dicto.es", password="pw")
        grammar_point_a1 = make_grammar_point(db_session, level="A1", slug="ser-estar", title="Ser/Estar")
        grammar_point_a2 = make_grammar_point(db_session, level="A2", slug="por-para", title="Por/Para")
        first_prompt = make_prompt(db_session, grammar_point=grammar_point_a1, answers=("es",))
        make_prompt(db_session, sentence="___ importante", grammar_point=grammar_point_a2, answers=("es",))
        make_review_state(db_session, user, first_prompt)

        flat = grammar_service.list_grammar_points(db_session)
        assert len(flat["items"]) == 2

        grouped = grammar_service.list_grammar_points_by_level(db_session, user)
        level_a1 = next(level for level in grouped["levels"] if level["level"] == "A1")
        assert level_a1["total_prompts"] == 1
        assert level_a1["in_queue"] == 1

    def test_get_grammar_point_handles_invalid_structure(self, db_session):
        user = make_user(db_session, email="svc-grammar-detail@dicto.es", password="pw")
        grammar_point = make_grammar_point(db_session, slug="detail-slug")
        grammar_point.structure = "not-json"
        db_session.commit()
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        make_review_state(
            db_session,
            user,
            prompt,
            due_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
        )

        service_output = grammar_service.get_grammar_point(db_session, user, grammar_point.id)
        assert service_output["structure"] == []
        assert service_output["mastery"]["total_prompts"] == 1

    def test_get_grammar_point_not_found(self, db_session):
        user = make_user(db_session, email="svc-grammar-missing@dicto.es", password="pw")
        with pytest.raises(ServiceError) as exc:
            grammar_service.get_grammar_point(db_session, user, 99999)
        assert exc.value.status_code == 404
