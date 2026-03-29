"""
Seed script: populates the database with initial Spanish learning content.

Usage (via Makefile):
    make seed

Direct usage inside container:
    python scripts/seed.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import SessionLocal
from app.models import GrammarPoint, GrammarExample, VocabItem, Prompt, PromptAnswer


# ---------------------------------------------------------------------------
# Load fixtures from JSON
# ---------------------------------------------------------------------------

def load_fixtures():
    """Load grammar points and vocab items from fixtures.json"""
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures.json")
    with open(fixtures_path, "r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    return data.get("grammar_points", []), data.get("vocab_items", [])


GRAMMAR_POINTS, VOCAB_ITEMS = load_fixtures()


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------

def seed_grammar(db_session) -> dict[str, int]:
    """Insert grammar points, examples, and grammar prompts. Returns slug→id map."""
    slug_to_id: dict[str, int] = {}
    created_grammar_points = 0
    created_examples = 0
    created_prompts = 0

    for grammar_fixture in GRAMMAR_POINTS:
        grammar_point = db_session.query(GrammarPoint).filter_by(slug=grammar_fixture["slug"]).first()
        if not grammar_point:
            structure = grammar_fixture.get("structure")
            if isinstance(structure, list):
                structure = json.dumps(structure)

            grammar_point = GrammarPoint(
                level=grammar_fixture["level"],
                slug=grammar_fixture["slug"],
                title=grammar_fixture["title"],
                short_description=grammar_fixture["short_description"],
                structure=structure,
                explanation=grammar_fixture["explanation"],
            )
            db_session.add(grammar_point)
            db_session.flush()
            created_grammar_points += 1

        slug_to_id[grammar_point.slug] = grammar_point.id

        for example in grammar_fixture["examples"]:
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
                created_examples += 1

        for prompt_data in grammar_fixture["prompts"]:
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
                created_prompts += 1

            for answer_text in prompt_data["answers"]:
                exists = db_session.query(PromptAnswer).filter_by(
                    prompt_id=prompt.id, answer=answer_text
                ).first()
                if not exists:
                    db_session.add(PromptAnswer(prompt_id=prompt.id, answer=answer_text))

    db_session.commit()
    print(f"  Grammar points:  {created_grammar_points} created")
    print(f"  Grammar examples: {created_examples} created")
    print(f"  Grammar prompts:  {created_prompts} created")
    return slug_to_id


def seed_vocab(db_session) -> None:
    """Insert vocab items and their prompts."""
    created_vocab_items = 0
    created_prompts = 0

    for vocab_fixture in VOCAB_ITEMS:
        vocab_item = db_session.query(VocabItem).filter_by(word=vocab_fixture["word"]).first()
        if not vocab_item:
            # Handle tags - could be array or string
            tags = vocab_fixture.get("tags")
            if isinstance(tags, list):
                tags = ",".join(tags)

            vocab_item = VocabItem(
                level=vocab_fixture["level"],
                word=vocab_fixture["word"],
                translation=vocab_fixture["translation"],
                part_of_speech=vocab_fixture.get("part_of_speech"),
                gender=vocab_fixture.get("gender"),
                example_sentence=vocab_fixture.get("example_sentence"),
                example_translation=vocab_fixture.get("example_translation"),
                tags=tags,
            )
            db_session.add(vocab_item)
            db_session.flush()
            created_vocab_items += 1

        for prompt_data in vocab_fixture.get("prompts", []):
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
                created_prompts += 1

            for answer_text in prompt_data["answers"]:
                exists = db_session.query(PromptAnswer).filter_by(
                    prompt_id=prompt.id, answer=answer_text
                ).first()
                if not exists:
                    db_session.add(PromptAnswer(prompt_id=prompt.id, answer=answer_text))

    db_session.commit()
    print(f"  Vocab items:  {created_vocab_items} created")
    print(f"  Vocab prompts: {created_prompts} created")


def main() -> None:
    print("Seeding database...")
    db_session = SessionLocal()
    try:
        seed_grammar(db_session)
        seed_vocab(db_session)
        print("Done.")
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
