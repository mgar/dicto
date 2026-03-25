"""Admin CRUD for grammar, vocab, prompts."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GrammarExample, GrammarPoint, Prompt, PromptAnswer, VocabItem
from app.schemas.admin import GrammarPointIn, PromptIn, VocabItemIn
from app.services.errors import ServiceError


def grammar_point_to_dict(grammar_point: GrammarPoint, include_examples: bool = False) -> dict:
    out = {
        "id": grammar_point.id,
        "level": grammar_point.level,
        "slug": grammar_point.slug,
        "title": grammar_point.title,
        "short_description": grammar_point.short_description,
        "structure": json.loads(grammar_point.structure) if grammar_point.structure else None,
        "explanation": grammar_point.explanation,
    }
    if include_examples:
        out["examples"] = [
            {
                "id": example.id,
                "sentence": example.sentence,
                "translation": example.translation,
                "highlight": example.highlight,
                "notes": example.notes,
                "sort_order": example.sort_order,
            }
            for example in sorted(
                grammar_point.examples, key=lambda example: example.sort_order
            )
        ]
    return out


def vocab_item_to_dict(vocab_item: VocabItem) -> dict:
    return {
        "id": vocab_item.id,
        "level": vocab_item.level,
        "word": vocab_item.word,
        "translation": vocab_item.translation,
        "part_of_speech": vocab_item.part_of_speech,
        "gender": vocab_item.gender,
        "example_sentence": vocab_item.example_sentence,
        "example_translation": vocab_item.example_translation,
        "notes": vocab_item.notes,
        "tags": vocab_item.tags,
    }

def prompt_to_admin_dict(prompt: Prompt) -> dict:
    grammar_point_title = prompt.grammar_point.title if prompt.grammar_point else None
    vocab_item_word = prompt.vocab_item.word if prompt.vocab_item else None
    return {
        "id": prompt.id,
        "kind": prompt.kind,
        "grammar_point_id": prompt.grammar_point_id,
        "grammar_point_title": grammar_point_title,
        "vocab_item_id": prompt.vocab_item_id,
        "vocab_item_word": vocab_item_word,
        "sentence": prompt.sentence,
        "notes": prompt.notes,
        "answers": [answer_row.answer for answer_row in prompt.answers],
    }


def admin_list_grammar_points(db_session: Session) -> dict:
    rows = db_session.execute(select(GrammarPoint).order_by(GrammarPoint.level, GrammarPoint.id)).scalars().all()
    return {
        "items": [grammar_point_to_dict(grammar_point_row) for grammar_point_row in rows]
    }


def admin_get_grammar_point(db_session: Session, grammar_point_id: int) -> dict:
    grammar_point = db_session.execute(select(GrammarPoint).where(GrammarPoint.id == grammar_point_id)).scalar_one_or_none()
    if not grammar_point:
        raise ServiceError(404, "Grammar point not found")
    return grammar_point_to_dict(grammar_point, include_examples=True)


def admin_create_grammar_point(db_session: Session, payload: GrammarPointIn) -> dict:
    existing = db_session.execute(
        select(GrammarPoint).where(GrammarPoint.slug == payload.slug)
    ).scalar_one_or_none()
    if existing:
        raise ServiceError(409, "Slug already in use")

    grammar_point = GrammarPoint(
        level=payload.level,
        slug=payload.slug,
        title=payload.title,
        short_description=payload.short_description,
        structure=json.dumps(payload.structure) if payload.structure else None,
        explanation=payload.explanation,
    )
    db_session.add(grammar_point)
    db_session.flush()

    for example_in in payload.examples:
        db_session.add(GrammarExample(
            grammar_point_id=grammar_point.id,
            sentence=example_in.sentence,
            translation=example_in.translation,
            highlight=example_in.highlight,
            notes=example_in.notes,
            sort_order=example_in.sort_order,
        ))

    db_session.commit()
    db_session.refresh(grammar_point)
    return grammar_point_to_dict(grammar_point, include_examples=True)


def admin_update_grammar_point(db_session: Session, grammar_point_id: int, payload: GrammarPointIn) -> dict:
    grammar_point = db_session.execute(select(GrammarPoint).where(GrammarPoint.id == grammar_point_id)).scalar_one_or_none()
    if not grammar_point:
        raise ServiceError(404, "Grammar point not found")

    if payload.slug != grammar_point.slug:
        conflict = db_session.execute(
            select(GrammarPoint).where(GrammarPoint.slug == payload.slug)
        ).scalar_one_or_none()
        if conflict:
            raise ServiceError(409, "Slug already in use")

    grammar_point.level = payload.level
    grammar_point.slug = payload.slug
    grammar_point.title = payload.title
    grammar_point.short_description = payload.short_description
    grammar_point.structure = json.dumps(payload.structure) if payload.structure else None
    grammar_point.explanation = payload.explanation

    for example in list(grammar_point.examples):
        db_session.delete(example)
    db_session.flush()
    for example_in in payload.examples:
        db_session.add(GrammarExample(
            grammar_point_id=grammar_point.id,
            sentence=example_in.sentence,
            translation=example_in.translation,
            highlight=example_in.highlight,
            notes=example_in.notes,
            sort_order=example_in.sort_order,
        ))

    db_session.commit()
    db_session.refresh(grammar_point)
    return grammar_point_to_dict(grammar_point, include_examples=True)


def admin_delete_grammar_point(db_session: Session, grammar_point_id: int) -> None:
    grammar_point = db_session.execute(select(GrammarPoint).where(GrammarPoint.id == grammar_point_id)).scalar_one_or_none()
    if not grammar_point:
        raise ServiceError(404, "Grammar point not found")
    db_session.delete(grammar_point)
    db_session.commit()


def admin_list_vocab_items(db_session: Session) -> dict:
    rows = db_session.execute(select(VocabItem).order_by(VocabItem.level, VocabItem.word)).scalars().all()
    return {"items": [vocab_item_to_dict(vocab_item) for vocab_item in rows]}


def admin_get_vocab_item(db_session: Session, vocab_item_id: int) -> dict:
    vocab_item = db_session.execute(select(VocabItem).where(VocabItem.id == vocab_item_id)).scalar_one_or_none()
    if not vocab_item:
        raise ServiceError(404, "Vocab item not found")
    return vocab_item_to_dict(vocab_item)


def admin_create_vocab_item(db_session: Session, payload: VocabItemIn) -> dict:
    vocab_item = VocabItem(
        level=payload.level,
        word=payload.word,
        translation=payload.translation,
        part_of_speech=payload.part_of_speech,
        gender=payload.gender,
        example_sentence=payload.example_sentence,
        example_translation=payload.example_translation,
        notes=payload.notes,
        tags=payload.tags,
    )
    db_session.add(vocab_item)
    db_session.commit()
    db_session.refresh(vocab_item)
    return vocab_item_to_dict(vocab_item)


def admin_update_vocab_item(db_session: Session, vocab_item_id: int, payload: VocabItemIn) -> dict:
    vocab_item = db_session.execute(select(VocabItem).where(VocabItem.id == vocab_item_id)).scalar_one_or_none()
    if not vocab_item:
        raise ServiceError(404, "Vocab item not found")

    vocab_item.level = payload.level
    vocab_item.word = payload.word
    vocab_item.translation = payload.translation
    vocab_item.part_of_speech = payload.part_of_speech
    vocab_item.gender = payload.gender
    vocab_item.example_sentence = payload.example_sentence
    vocab_item.example_translation = payload.example_translation
    vocab_item.notes = payload.notes
    vocab_item.tags = payload.tags

    db_session.commit()
    db_session.refresh(vocab_item)
    return vocab_item_to_dict(vocab_item)


def admin_delete_vocab_item(db_session: Session, vocab_item_id: int) -> None:
    vocab_item = db_session.execute(select(VocabItem).where(VocabItem.id == vocab_item_id)).scalar_one_or_none()
    if not vocab_item:
        raise ServiceError(404, "Vocab item not found")
    db_session.delete(vocab_item)
    db_session.commit()


def admin_list_prompts(db_session: Session, kind: str | None) -> dict:
    stmt = select(Prompt).order_by(Prompt.kind, Prompt.id)
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    rows = db_session.execute(stmt).scalars().all()
    return {"items": [prompt_to_admin_dict(prompt_row) for prompt_row in rows]}


def admin_get_prompt(db_session: Session, prompt_id: int) -> dict:
    prompt = db_session.execute(select(Prompt).where(Prompt.id == prompt_id)).scalar_one_or_none()
    if not prompt:
        raise ServiceError(404, "Prompt not found")
    return prompt_to_admin_dict(prompt)


def admin_create_prompt(db_session: Session, payload: PromptIn) -> dict:
    if not payload.answers:
        raise ServiceError(422, "At least one answer is required")
    if "___" not in payload.sentence:
        raise ServiceError(422, "Sentence must contain ___ for the cloze blank")

    prompt = Prompt(
        grammar_point_id=payload.grammar_point_id,
        vocab_item_id=payload.vocab_item_id,
        kind=payload.kind,
        sentence=payload.sentence,
        notes=payload.notes,
    )
    db_session.add(prompt)
    db_session.flush()

    for answer in payload.answers:
        db_session.add(PromptAnswer(prompt_id=prompt.id, answer=answer.strip()))

    db_session.commit()
    db_session.refresh(prompt)
    return prompt_to_admin_dict(prompt)


def admin_update_prompt(db_session: Session, prompt_id: int, payload: PromptIn) -> dict:
    prompt = db_session.execute(select(Prompt).where(Prompt.id == prompt_id)).scalar_one_or_none()
    if not prompt:
        raise ServiceError(404, "Prompt not found")

    if not payload.answers:
        raise ServiceError(422, "At least one answer is required")
    if "___" not in payload.sentence:
        raise ServiceError(422, "Sentence must contain ___ for the cloze blank")

    prompt.grammar_point_id = payload.grammar_point_id
    prompt.vocab_item_id = payload.vocab_item_id
    prompt.kind = payload.kind
    prompt.sentence = payload.sentence
    prompt.notes = payload.notes

    for answer_row in list(prompt.answers):
        db_session.delete(answer_row)
    db_session.flush()
    for answer in payload.answers:
        db_session.add(PromptAnswer(prompt_id=prompt.id, answer=answer.strip()))

    db_session.commit()
    db_session.refresh(prompt)
    return prompt_to_admin_dict(prompt)


def admin_delete_prompt(db_session: Session, prompt_id: int) -> None:
    prompt = db_session.execute(select(Prompt).where(Prompt.id == prompt_id)).scalar_one_or_none()
    if not prompt:
        raise ServiceError(404, "Prompt not found")
    db_session.delete(prompt)
    db_session.commit()
