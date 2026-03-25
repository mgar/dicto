"""Learning queue, study flow, preferences, auto-add."""
import json
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import GrammarExample, GrammarPoint, Prompt, ReviewState, User, VocabItem
from app.schemas.learn import LearnNextOut, MarkStudiedIn, PreferencesIn
from app.services.errors import ServiceError
from app.utils import prompt_to_dict

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _new_learning_state(user_id: int, prompt_id: int, due_now) -> ReviewState:
    return ReviewState(
        user_id=user_id,
        prompt_id=prompt_id,
        ease_factor=2.5,
        interval_days=0,
        repetitions=0,
        due_at=due_now,
        last_reviewed_at=None,
        status="learning",
    )


def get_learn_levels(db_session: Session, user: User) -> dict:
    levels_data = []
    for level in CEFR_LEVELS:
        grammar_count = db_session.execute(
            select(func.count()).select_from(GrammarPoint).where(GrammarPoint.level == level)
        ).scalar_one()

        vocab_count = db_session.execute(
            select(func.count()).select_from(VocabItem).where(VocabItem.level == level)
        ).scalar_one()

        grammar_prompts = db_session.execute(
            select(func.count())
            .select_from(Prompt)
            .join(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .where(GrammarPoint.level == level)
        ).scalar_one()

        vocab_prompts = db_session.execute(
            select(func.count())
            .select_from(Prompt)
            .join(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .where(VocabItem.level == level)
        ).scalar_one()

        total_prompts = grammar_prompts + vocab_prompts

        grammar_in_queue = db_session.execute(
            select(func.count())
            .select_from(ReviewState)
            .join(Prompt, Prompt.id == ReviewState.prompt_id)
            .join(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .where(and_(ReviewState.user_id == user.id, GrammarPoint.level == level))
        ).scalar_one()

        vocab_in_queue = db_session.execute(
            select(func.count())
            .select_from(ReviewState)
            .join(Prompt, Prompt.id == ReviewState.prompt_id)
            .join(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .where(and_(ReviewState.user_id == user.id, VocabItem.level == level))
        ).scalar_one()

        in_queue = grammar_in_queue + vocab_in_queue

        levels_data.append({
            "level": level,
            "grammar_points": grammar_count,
            "vocab_items": vocab_count,
            "total_prompts": total_prompts,
            "in_queue": in_queue,
            "fully_added": in_queue >= total_prompts and total_prompts > 0,
        })

    total_in_queue = db_session.execute(
        select(func.count()).select_from(ReviewState).where(ReviewState.user_id == user.id)
    ).scalar_one()

    return {"levels": levels_data, "total_in_queue": total_in_queue}


def learn_count(db_session: Session, user: User, kind: str | None) -> dict:
    stmt = (
        select(func.count())
        .select_from(ReviewState)
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "learning",
            )
        )
    )
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    remaining = int(db_session.execute(stmt).scalar_one())
    return {"remaining": remaining}


def learn_queue(db_session: Session, user: User, limit: int, kind: str | None) -> dict:
    stmt = (
        select(Prompt, GrammarPoint, VocabItem)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .outerjoin(
            ReviewState,
            and_(
                ReviewState.user_id == user.id,
                ReviewState.prompt_id == Prompt.id,
            ),
        )
        .where(ReviewState.prompt_id.is_(None))
    )
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    stmt = stmt.order_by(Prompt.id.asc()).limit(limit)

    rows = db_session.execute(stmt).all()
    items = [prompt_to_dict(prompt, grammar_point, vocab_item) for (prompt, grammar_point, vocab_item) in rows]

    available_stmt = (
        select(func.count())
        .select_from(Prompt)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(ReviewState.prompt_id.is_(None))
    )
    if kind:
        available_stmt = available_stmt.where(Prompt.kind == kind)
    available_to_add = int(db_session.execute(available_stmt).scalar_one())

    new_in_queue_stmt = (
        select(func.count())
        .select_from(ReviewState)
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "learning",
            )
        )
    )
    if kind:
        new_in_queue_stmt = new_in_queue_stmt.where(Prompt.kind == kind)
    new_in_queue = int(db_session.execute(new_in_queue_stmt).scalar_one())

    return {
        "items": items,
        "remaining": available_to_add,
        "available_to_add": available_to_add,
        "new_in_queue": new_in_queue,
    }


def learn_next(db_session: Session, user: User, count: int, kind: str | None) -> dict:
    if count < 1:
        raise ServiceError(400, "count must be >= 1")
    if count > 50:
        raise ServiceError(400, "count too large")

    stmt = (
        select(Prompt, GrammarPoint, VocabItem)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .outerjoin(
            ReviewState,
            and_(
                ReviewState.user_id == user.id,
                ReviewState.prompt_id == Prompt.id,
            ),
        )
        .where(ReviewState.prompt_id.is_(None))
    )
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    stmt = stmt.order_by(Prompt.id.asc()).limit(count)

    rows = db_session.execute(stmt).all()
    due_now = now_utc().replace(tzinfo=None)

    added_items = []
    for (prompt, grammar_point, vocab_item) in rows:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now))
        added_items.append(prompt_to_dict(prompt, grammar_point, vocab_item))

    db_session.commit()

    remaining_stmt = (
        select(func.count())
        .select_from(Prompt)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(ReviewState.prompt_id.is_(None))
    )
    if kind:
        remaining_stmt = remaining_stmt.where(Prompt.kind == kind)
    remaining = int(db_session.execute(remaining_stmt).scalar_one())

    return LearnNextOut(added=added_items, remaining=remaining).model_dump()


def learn_add_grammar_point(db_session: Session, user: User, grammar_point_id: int) -> dict:
    grammar_point = db_session.execute(
        select(GrammarPoint).where(GrammarPoint.id == grammar_point_id)
    ).scalar_one_or_none()
    if not grammar_point:
        raise ServiceError(404, "Grammar point not found")

    stmt = (
        select(Prompt)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(
            and_(
                Prompt.grammar_point_id == grammar_point_id,
                ReviewState.prompt_id.is_(None),
            )
        )
    )
    prompts = db_session.execute(stmt).scalars().all()
    due_now = now_utc().replace(tzinfo=None)

    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now))
        added_count += 1

    db_session.commit()
    return {
        "added": added_count,
        "grammar_point_id": grammar_point_id,
        "grammar_point_title": grammar_point.title,
    }


def learn_add_vocab_item(db_session: Session, user: User, vocab_item_id: int) -> dict:
    vocab_item = db_session.execute(select(VocabItem).where(VocabItem.id == vocab_item_id)).scalar_one_or_none()
    if not vocab_item:
        raise ServiceError(404, "Vocab item not found")

    stmt = (
        select(Prompt)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(
            and_(
                Prompt.vocab_item_id == vocab_item_id,
                ReviewState.prompt_id.is_(None),
            )
        )
    )
    prompts = db_session.execute(stmt).scalars().all()
    due_now = now_utc().replace(tzinfo=None)

    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now))
        added_count += 1

    db_session.commit()
    return {"added": added_count, "vocab_item_id": vocab_item_id, "vocab_word": vocab_item.word}


def learn_add_level(
    db_session: Session, user: User, level: str, kind: str | None, limit: int | None
) -> dict:
    if level.upper() not in CEFR_LEVELS:
        raise ServiceError(400, f"Invalid level. Must be one of: {', '.join(CEFR_LEVELS)}")

    level = level.upper()

    if kind is None and limit is not None and limit > 0:
        grammar_limit = (limit + 1) // 2
        grammar_stmt = (
            select(Prompt)
            .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .outerjoin(
                ReviewState,
                and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
            )
            .where(
                and_(
                    ReviewState.prompt_id.is_(None),
                    GrammarPoint.level == level,
                    Prompt.kind == "grammar",
                )
            )
            .order_by(Prompt.id.asc())
            .limit(grammar_limit)
        )
        grammar_prompts = db_session.execute(grammar_stmt).scalars().all()

        vocab_limit = limit - len(grammar_prompts)
        vocab_stmt = (
            select(Prompt)
            .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .outerjoin(
                ReviewState,
                and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
            )
            .where(
                and_(
                    ReviewState.prompt_id.is_(None),
                    VocabItem.level == level,
                    Prompt.kind == "vocab",
                )
            )
            .order_by(Prompt.id.asc())
            .limit(vocab_limit)
        )
        vocab_prompts = db_session.execute(vocab_stmt).scalars().all()
        prompts = list(grammar_prompts) + list(vocab_prompts)
    else:
        stmt = (
            select(Prompt)
            .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .outerjoin(
                ReviewState,
                and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
            )
            .where(
                and_(
                    ReviewState.prompt_id.is_(None),
                    ((GrammarPoint.level == level) | (VocabItem.level == level)),
                )
            )
            .order_by(Prompt.id.asc())
        )
        if kind:
            stmt = stmt.where(Prompt.kind == kind)
        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)
        prompts = db_session.execute(stmt).scalars().all()

    due_now = now_utc().replace(tzinfo=None)
    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now))
        added_count += 1

    db_session.commit()
    return {"added": added_count, "level": level, "kind": kind}


def get_study_queue(db_session: Session, user: User) -> dict:
    stmt = (
        select(ReviewState, Prompt, GrammarPoint, VocabItem)
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "learning",
            )
        )
        .order_by(ReviewState.due_at.asc())
    )
    rows = db_session.execute(stmt).all()

    seen_grammar: set[int] = set()
    seen_vocab: set[int] = set()
    items: list[dict] = []

    for (_unused_review_state, prompt, grammar_point, vocab_item) in rows:
        if prompt.kind == "grammar" and grammar_point:
            if grammar_point.id in seen_grammar:
                continue
            seen_grammar.add(grammar_point.id)

            examples_stmt = (
                select(GrammarExample)
                .where(GrammarExample.grammar_point_id == grammar_point.id)
                .order_by(GrammarExample.sort_order)
            )
            examples = db_session.execute(examples_stmt).scalars().all()

            structure: list = []
            if grammar_point.structure:
                try:
                    structure = json.loads(grammar_point.structure)
                except json.JSONDecodeError:
                    structure = []

            items.append({
                "kind": "grammar",
                "grammar_point_id": grammar_point.id,
                "grammar_title": grammar_point.title,
                "grammar_level": grammar_point.level,
                "grammar_description": grammar_point.short_description,
                "grammar_explanation": grammar_point.explanation,
                "grammar_structure": structure,
                "grammar_examples": [
                    {
                        "id": example.id,
                        "sentence": example.sentence,
                        "translation": example.translation,
                        "highlight": example.highlight,
                        "notes": example.notes,
                    }
                    for example in examples
                ],
            })

        elif prompt.kind == "vocab" and vocab_item:
            if vocab_item.id in seen_vocab:
                continue
            seen_vocab.add(vocab_item.id)

            items.append({
                "kind": "vocab",
                "vocab_item_id": vocab_item.id,
                "vocab_word": vocab_item.word,
                "vocab_level": vocab_item.level,
                "vocab_translation": vocab_item.translation,
                "vocab_pos": vocab_item.part_of_speech,
                "vocab_gender": vocab_item.gender,
                "vocab_example": vocab_item.example_sentence,
                "vocab_example_translation": vocab_item.example_translation,
                "vocab_notes": vocab_item.notes,
            })

    return {"items": items}


def mark_items_studied(db_session: Session, user: User, payload: MarkStudiedIn | None) -> dict:
    if payload and payload.local_date:
        try:
            local_today = datetime.fromisoformat(payload.local_date).date()
            due_at = datetime.combine(local_today, time(0, 0, 0))
        except ValueError:
            due_at = now_utc().replace(tzinfo=None)
    else:
        due_at = now_utc().replace(tzinfo=None)

    stmt = select(ReviewState).where(
        and_(
            ReviewState.user_id == user.id,
            ReviewState.status == "learning",
        )
    )
    states = db_session.execute(stmt).scalars().all()
    count = 0
    for review_state in states:
        review_state.status = "reviewing"
        review_state.due_at = due_at
        count += 1

    db_session.commit()
    return {"marked": count}


def save_preferences(db_session: Session, user: User, prefs: PreferencesIn) -> dict:
    if prefs.daily_new_limit < 1 or prefs.daily_new_limit > 50:
        raise ServiceError(400, "Daily limit must be between 1 and 50")
    if prefs.content_preference not in ["both", "grammar", "vocab"]:
        raise ServiceError(400, "Content preference must be 'both', 'grammar', or 'vocab'")
    for level in prefs.selected_levels:
        if level not in CEFR_LEVELS:
            raise ServiceError(400, f"Invalid level: {level}")

    user.daily_new_limit = prefs.daily_new_limit
    user.content_preference = prefs.content_preference
    user.selected_levels = ",".join(prefs.selected_levels)
    db_session.commit()
    return {"message": "Preferences saved successfully"}


def auto_add_items(db_session: Session, user: User, tz_offset: int | None) -> dict:
    if not user.daily_new_limit or not user.selected_levels:
        raise ServiceError(
            400,
            "No learning preferences set. Please configure your daily goal first.",
        )

    offset_minutes = -(tz_offset or 0)
    user_tz = timezone(timedelta(minutes=offset_minutes))
    local_today = datetime.now(user_tz).date()

    if user.last_items_added_at:
        last_added_utc = user.last_items_added_at.replace(tzinfo=timezone.utc)
        last_added_local = last_added_utc.astimezone(user_tz).date()
        if last_added_local >= local_today:
            return {
                "added": 0,
                "message": "New items already added today. Come back tomorrow!",
                "already_added_today": True,
            }

    unstudied_count = db_session.execute(
        select(func.count())
        .select_from(ReviewState)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "learning",
            )
        )
    ).scalar_one()

    if unstudied_count > 0:
        return {
            "added": 0,
            "message": f"You still have {unstudied_count} unstudied items. Complete them before getting new items.",
            "unstudied_count": unstudied_count,
        }

    levels = user.selected_levels.split(",")
    limit = user.daily_new_limit
    kind = None if user.content_preference == "both" else user.content_preference

    if kind is None:
        grammar_limit = (limit + 1) // 2
        grammar_stmt = (
            select(Prompt)
            .join(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .outerjoin(
                ReviewState,
                and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
            )
            .where(
                and_(
                    ReviewState.prompt_id.is_(None),
                    GrammarPoint.level.in_(levels),
                    Prompt.kind == "grammar",
                )
            )
            .order_by(Prompt.id.asc())
            .limit(grammar_limit)
        )
        grammar_prompts = db_session.execute(grammar_stmt).scalars().all()

        vocab_limit = limit - len(grammar_prompts)
        vocab_stmt = (
            select(Prompt)
            .join(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .outerjoin(
                ReviewState,
                and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
            )
            .where(
                and_(
                    ReviewState.prompt_id.is_(None),
                    VocabItem.level.in_(levels),
                    Prompt.kind == "vocab",
                )
            )
            .order_by(Prompt.id.asc())
            .limit(vocab_limit)
        )
        vocab_prompts = db_session.execute(vocab_stmt).scalars().all()
        prompts = list(grammar_prompts) + list(vocab_prompts)
    else:
        stmt = (
            select(Prompt)
            .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .outerjoin(
                ReviewState,
                and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
            )
            .where(
                and_(
                    ReviewState.prompt_id.is_(None),
                    or_(
                        GrammarPoint.level.in_(levels),
                        VocabItem.level.in_(levels),
                    ),
                    Prompt.kind == kind,
                )
            )
            .order_by(Prompt.id.asc())
            .limit(limit)
        )
        prompts = db_session.execute(stmt).scalars().all()

    due_now = now_utc().replace(tzinfo=None)
    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now))
        added_count += 1

    if added_count > 0:
        user.last_items_added_at = now_utc().replace(tzinfo=None)

    db_session.commit()

    return {
        "added": added_count,
        "message": f"Added {added_count} new items to your queue" if added_count > 0 else "No new items available",
    }
