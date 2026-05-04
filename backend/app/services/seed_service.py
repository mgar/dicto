"""
Content seeding service.

Populates the database with the initial learning content from
scripts/fixtures.json. All operations are idempotent so existing rows are
skipped and this is safe to call on every startup.

Called automatically from the app lifespan (main.py) and can also be invoked
directly via `make seed` (scripts/seed.py).
"""
import json
from pathlib import Path

from app.db import SessionLocal
from app.models import GrammarExample, GrammarPoint, Prompt, PromptAnswer, VocabItem

_FIXTURES_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "fixtures.json"


def _load_fixtures() -> tuple[list, list]:
    with open(_FIXTURES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("grammar_points", []), data.get("vocab_items", [])


def _sync_prompt_answers(db_session, prompt: Prompt, answers: list[str]) -> None:
    desired_answers = {answer for answer in answers if answer}
    existing_answers = db_session.query(PromptAnswer).filter_by(prompt_id=prompt.id).all()

    for answer_row in existing_answers:
        if answer_row.answer not in desired_answers:
            db_session.delete(answer_row)

    existing_answer_texts = {answer_row.answer for answer_row in existing_answers}
    for answer_text in desired_answers - existing_answer_texts:
        db_session.add(PromptAnswer(prompt_id=prompt.id, answer=answer_text))


def _seed_grammar(db_session, grammar_points: list) -> None:
    for gp_data in grammar_points:
        grammar_point = db_session.query(GrammarPoint).filter_by(slug=gp_data["slug"]).first()
        if not grammar_point:
            structure = gp_data.get("structure")
            if isinstance(structure, list):
                structure = json.dumps(structure)
            grammar_point = GrammarPoint(
                level=gp_data["level"],
                slug=gp_data["slug"],
                title=gp_data["title"],
                short_description=gp_data["short_description"],
                structure=structure,
                explanation=gp_data["explanation"],
            )
            db_session.add(grammar_point)
            db_session.flush()

        for example in gp_data["examples"]:
            exists = db_session.query(GrammarExample).filter_by(
                grammar_point_id=grammar_point.id, sort_order=example["sort_order"]
            ).first()
            if not exists:
                db_session.add(GrammarExample(
                    grammar_point_id=grammar_point.id,
                    sentence=example["sentence"],
                    translation=example["translation"],
                    highlight=example["highlight"],
                    sort_order=example["sort_order"],
                ))

        for prompt_data in gp_data["prompts"]:
            prompt = db_session.query(Prompt).filter_by(
                sentence=prompt_data["sentence"], kind="grammar"
            ).first()
            if not prompt:
                prompt = Prompt(
                    grammar_point_id=grammar_point.id,
                    kind="grammar",
                    sentence=prompt_data["sentence"],
                    notes=prompt_data.get("notes"),
                )
                db_session.add(prompt)
                db_session.flush()

            _sync_prompt_answers(db_session, prompt, prompt_data["answers"])

    db_session.commit()


def _seed_vocab(db_session, vocab_items: list) -> None:
    for vocab_data in vocab_items:
        vocab_item = db_session.query(VocabItem).filter_by(word=vocab_data["word"]).first()
        if not vocab_item:
            tags = vocab_data.get("tags")
            if isinstance(tags, list):
                tags = ",".join(tags)
            vocab_item = VocabItem(
                level=vocab_data["level"],
                word=vocab_data["word"],
                translation=vocab_data["translation"],
                part_of_speech=vocab_data.get("part_of_speech"),
                gender=vocab_data.get("gender"),
                example_sentence=vocab_data.get("example_sentence"),
                example_translation=vocab_data.get("example_translation"),
                tags=tags,
            )
            db_session.add(vocab_item)
            db_session.flush()

        for prompt_data in vocab_data.get("prompts", []):
            prompt = db_session.query(Prompt).filter_by(
                sentence=prompt_data["sentence"], kind="vocab"
            ).first()
            if not prompt:
                prompt = Prompt(
                    vocab_item_id=vocab_item.id,
                    kind="vocab",
                    sentence=prompt_data["sentence"],
                    notes=prompt_data.get("notes"),
                )
                db_session.add(prompt)
                db_session.flush()

            _sync_prompt_answers(db_session, prompt, prompt_data["answers"])

    db_session.commit()


def seed_content() -> None:
    """Seed the database with Spanish learning content. Safe to call on every startup."""
    grammar_points, vocab_items = _load_fixtures()
    db_session = SessionLocal()
    try:
        _seed_grammar(db_session, grammar_points)
        _seed_vocab(db_session, vocab_items)
    finally:
        db_session.close()
