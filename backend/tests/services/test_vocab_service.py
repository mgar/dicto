import pytest

from app.services import vocab_service
from app.services.errors import ServiceError
from tests.conftest import make_prompt, make_user, make_vocab_item
from tests.services.helpers import make_review_state


class TestVocabService:
    def test_list_vocab_items_filters(self, db_session):
        make_vocab_item(db_session, word="casa", level="A1")
        item = make_vocab_item(db_session, word="coche", level="A2")
        item.tags = "transport"
        db_session.commit()

        service_output = vocab_service.list_vocab_items(db_session, level="A2", tag="transport")
        assert len(service_output["items"]) == 1
        assert service_output["items"][0]["word"] == "coche"

    def test_vocab_level_and_detail_mastery(self, db_session):
        user = make_user(db_session, email="svc-vocab@dicto.es", password="pw")
        vocab = make_vocab_item(db_session, word="agua", level="A1")
        prompt = make_prompt(
            db_session,
            kind="vocab",
            sentence="Bebo ___ todos los días.",
            vocab_item=vocab,
            answers=("agua",),
        )
        make_review_state(db_session, user, prompt)

        grouped_output = vocab_service.list_vocab_items_by_level(db_session, user)
        a1_level = next(level for level in grouped_output["levels"] if level["level"] == "A1")
        assert a1_level["in_queue"] == 1

        detail_output = vocab_service.get_vocab_item(db_session, user, vocab.id)
        assert detail_output["mastery"]["total_prompts"] == 1

    def test_get_vocab_item_not_found(self, db_session):
        user = make_user(db_session, email="svc-vocab-missing@dicto.es", password="pw")
        with pytest.raises(ServiceError) as exc:
            vocab_service.get_vocab_item(db_session, user, 99999)
        assert exc.value.status_code == 404
