"""
Tests for /api/admin/* endpoints.
Covers auth enforcement, CRUD operations, and validation rules.
"""
import pytest
from tests.conftest import (
    make_user, make_session, make_grammar_point, make_vocab_item, make_prompt, COOKIE_NAME
)


def auth_client(client, db_session, is_admin=True):
    """Return a client with a valid session cookie for an admin or regular user."""
    email = "admin-api@dicto.es" if is_admin else "user-api@dicto.es"
    user = make_user(db_session, email=email, password="pw", is_admin=is_admin)
    session_id = make_session(db_session, user)
    client.cookies.set(COOKIE_NAME, session_id)
    return client


# ============================================================
# Auth enforcement
# ============================================================

class TestAdminAuthEnforcement:
    def test_unauthenticated_is_401(self, client):
        response = client.get("/api/admin/grammar-points")
        assert response.status_code == 401

    def test_non_admin_is_403(self, client, db_session):
        auth_client(client, db_session, is_admin=False)
        response = client.get("/api/admin/grammar-points")
        assert response.status_code == 403


# ============================================================
# Grammar Points CRUD
# ============================================================

class TestAdminGrammarPoints:
    def setup_admin(self, client, db_session):
        return auth_client(client, db_session, is_admin=True)

    def test_list_empty(self, client, db_session):
        self.setup_admin(client, db_session)
        response = client.get("/api/admin/grammar-points")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_create(self, client, db_session):
        self.setup_admin(client, db_session)
        payload = {
            "level": "A1", "slug": "ser-estar", "title": "Ser vs Estar",
            "short_description": "To be.", "explanation": "Use ser for permanent states.",
            "structure": ["Noun + ser"], "examples": []
        }
        response = client.post("/api/admin/grammar-points", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "ser-estar"
        assert data["structure"] == ["Noun + ser"]

    def test_create_duplicate_slug_is_409(self, client, db_session):
        self.setup_admin(client, db_session)
        make_grammar_point(db_session)
        payload = {
            "level": "A1", "slug": "ser-estar", "title": "Other",
            "short_description": "x", "explanation": "y", "examples": []
        }
        response = client.post("/api/admin/grammar-points", json=payload)
        assert response.status_code == 409

    def test_get(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        response = client.get(f"/api/admin/grammar-points/{grammar_point.id}")
        assert response.status_code == 200
        assert response.json()["id"] == grammar_point.id

    def test_get_not_found(self, client, db_session):
        self.setup_admin(client, db_session)
        response = client.get("/api/admin/grammar-points/9999")
        assert response.status_code == 404

    def test_update(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        payload = {
            "level": "B1", "slug": "ser-estar", "title": "Updated Title",
            "short_description": "x", "explanation": "y", "examples": []
        }
        response = client.put(f"/api/admin/grammar-points/{grammar_point.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        assert response.json()["level"] == "B1"

    def test_update_with_examples(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        payload = {
            "level": "A1", "slug": "ser-estar", "title": "Ser vs Estar",
            "short_description": "x", "explanation": "y",
            "examples": [{"sentence": "Soy de España.", "translation": "I am from Spain.", "sort_order": 0}]
        }
        response = client.put(f"/api/admin/grammar-points/{grammar_point.id}", json=payload)
        assert response.status_code == 200
        assert len(response.json()["examples"]) == 1

    def test_delete(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        delete_response = client.delete(f"/api/admin/grammar-points/{grammar_point.id}")
        assert delete_response.status_code == 204
        get_response = client.get(f"/api/admin/grammar-points/{grammar_point.id}")
        assert get_response.status_code == 404


# ============================================================
# Vocab Items CRUD
# ============================================================

class TestAdminVocabItems:
    def setup_admin(self, client, db_session):
        return auth_client(client, db_session, is_admin=True)

    def test_create(self, client, db_session):
        self.setup_admin(client, db_session)
        payload = {"level": "A1", "word": "casa", "translation": "house",
                   "part_of_speech": "noun", "gender": "f"}
        response = client.post("/api/admin/vocab-items", json=payload)
        assert response.status_code == 201
        assert response.json()["word"] == "casa"

    def test_update(self, client, db_session):
        self.setup_admin(client, db_session)
        vocab_item = make_vocab_item(db_session)
        payload = {"level": "B1", "word": "hogar", "translation": "home"}
        response = client.put(f"/api/admin/vocab-items/{vocab_item.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["word"] == "hogar"

    def test_delete(self, client, db_session):
        self.setup_admin(client, db_session)
        vocab_item = make_vocab_item(db_session)
        response = client.delete(f"/api/admin/vocab-items/{vocab_item.id}")
        assert response.status_code == 204

    def test_get_not_found(self, client, db_session):
        self.setup_admin(client, db_session)
        response = client.get("/api/admin/vocab-items/9999")
        assert response.status_code == 404


# ============================================================
# Prompts CRUD
# ============================================================

class TestAdminPrompts:
    def setup_admin(self, client, db_session):
        return auth_client(client, db_session, is_admin=True)

    def test_create_grammar_prompt(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        payload = {
            "kind": "grammar", "grammar_point_id": grammar_point.id, "vocab_item_id": None,
            "sentence": "Ella ___ de Madrid.", "answers": ["es", "está"], "notes": None
        }
        response = client.post("/api/admin/prompts", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["grammar_point_id"] == grammar_point.id
        assert set(data["answers"]) == {"es", "está"}

    def test_create_requires_blank(self, client, db_session):
        self.setup_admin(client, db_session)
        payload = {
            "kind": "grammar", "grammar_point_id": None, "vocab_item_id": None,
            "sentence": "No blank here.", "answers": ["nada"]
        }
        response = client.post("/api/admin/prompts", json=payload)
        assert response.status_code == 422

    def test_create_requires_at_least_one_answer(self, client, db_session):
        self.setup_admin(client, db_session)
        payload = {
            "kind": "grammar", "grammar_point_id": None, "vocab_item_id": None,
            "sentence": "Ella ___ aquí.", "answers": []
        }
        response = client.post("/api/admin/prompts", json=payload)
        assert response.status_code == 422

    def test_update_replaces_answers(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        prompt = make_prompt(db_session, grammar_point=grammar_point, answers=("es",))
        payload = {
            "kind": "grammar", "grammar_point_id": grammar_point.id, "vocab_item_id": None,
            "sentence": "Ella ___ de Madrid.", "answers": ["está"], "notes": None
        }
        response = client.put(f"/api/admin/prompts/{prompt.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["answers"] == ["está"]

    def test_delete(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        prompt = make_prompt(db_session, grammar_point=grammar_point)
        response = client.delete(f"/api/admin/prompts/{prompt.id}")
        assert response.status_code == 204

    def test_filter_by_kind(self, client, db_session):
        self.setup_admin(client, db_session)
        grammar_point = make_grammar_point(db_session)
        vocab_item = make_vocab_item(db_session)
        make_prompt(db_session, kind="grammar", grammar_point=grammar_point)
        make_prompt(db_session, sentence="La ___ es grande.", kind="vocab", vocab_item=vocab_item, answers=("casa",))
        response = client.get("/api/admin/prompts?kind=vocab")
        assert response.status_code == 200
        items = response.json()["items"]
        assert all(item["kind"] == "vocab" for item in items)
        assert len(items) == 1
