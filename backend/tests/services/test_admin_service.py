import pytest

from app.schemas.admin import PromptIn
from app.services import admin_service
from app.services.errors import ServiceError


class TestAdminService:
    def test_admin_prompt_validation(self, db_session):
        payload = PromptIn(kind="grammar", sentence="No blank", answers=["x"])
        with pytest.raises(ServiceError) as exc:
            admin_service.admin_create_prompt(db_session, payload)
        assert exc.value.status_code == 422

    def test_admin_get_vocab_item_not_found(self, db_session):
        with pytest.raises(ServiceError) as exc:
            admin_service.admin_get_vocab_item(db_session, 99999)
        assert exc.value.status_code == 404
