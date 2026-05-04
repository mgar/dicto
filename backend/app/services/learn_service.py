"""Learning queue, study flow, preferences, auto-add."""
import json

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import GrammarExample, GrammarPoint, Prompt, ReviewState, User, VocabItem
from app.schemas.learn import LearnNextOut, PreferencesIn
from app.services.errors import ServiceError
from app.timezone_utils import local_date_from_utc
from app.utils import prompt_to_dict

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _selected_levels(user: User) -> list[str]:
    if not user.selected_levels:
        return []
    return [level for level in user.selected_levels.split(",") if level]


def _add_selected_level(user: User, level: str) -> None:
    levels = _selected_levels(user)
    if level not in levels:
        levels.append(level)
    user.selected_levels = ",".join(levels)


def _remove_selected_level(user: User, level: str) -> None:
    levels = [selected_level for selected_level in _selected_levels(user) if selected_level != level]
    user.selected_levels = ",".join(levels)


def _daily_limit(user: User, limit: int | None) -> int:
    if limit is not None:
        if limit < 1 or limit > 50:
            raise ServiceError(400, "Daily limit must be between 1 and 50")
        return limit
    if user.daily_new_limit:
        return user.daily_new_limit
    raise ServiceError(
        400,
        "No daily learning limit set. Please configure your daily goal first.",
    )


def _new_learning_state(user_id: int, prompt_id: int, due_now, introduced_local_date=None) -> ReviewState:
    return ReviewState(
        user_id=user_id,
        prompt_id=prompt_id,
        ease_factor=2.5,
        interval_days=0,
        repetitions=0,
        due_at=due_now,
        last_reviewed_at=None,
        introduced_at=due_now,
        introduced_local_date=introduced_local_date,
        status="learning",
    )


def _introduced_today_count(db_session: Session, user: User, local_today) -> int:
    return int(db_session.execute(
        select(func.count())
        .select_from(ReviewState)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.introduced_local_date == local_today,
            )
        )
    ).scalar_one())


def _learning_item_count(db_session: Session, user: User, kind: str | None = None) -> int:
    stmt = (
        select(
            Prompt.id,
            Prompt.kind,
            Prompt.grammar_point_id,
            Prompt.vocab_item_id,
        )
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

    item_keys = set()
    for prompt_id, prompt_kind, grammar_point_id, vocab_item_id in db_session.execute(stmt).all():
        if prompt_kind == "grammar" and grammar_point_id is not None:
            item_keys.add(("grammar", grammar_point_id))
        elif prompt_kind == "vocab" and vocab_item_id is not None:
            item_keys.add(("vocab", vocab_item_id))
        else:
            item_keys.add((prompt_kind, prompt_id))
    return len(item_keys)


def _select_unseen_prompts(
    db_session: Session,
    user: User,
    levels: list[str],
    limit: int,
    *,
    kind: str | None = None,
    exclude_prompt_ids: set[int] | None = None,
) -> list[Prompt]:
    if limit <= 0:
        return []

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
                or_(GrammarPoint.level.in_(levels), VocabItem.level.in_(levels)),
            )
        )
        .order_by(Prompt.id.asc())
        .limit(limit)
    )
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    if exclude_prompt_ids:
        stmt = stmt.where(Prompt.id.not_in(exclude_prompt_ids))

    return list(db_session.execute(stmt).scalars().all())


def get_learn_levels(db_session: Session, user: User) -> dict:
    grammar_counts = {
        level: count
        for level, count in db_session.execute(
            select(GrammarPoint.level, func.count()).group_by(GrammarPoint.level)
        ).all()
    }
    vocab_counts = {
        level: count
        for level, count in db_session.execute(
            select(VocabItem.level, func.count()).group_by(VocabItem.level)
        ).all()
    }

    prompt_counts = {
        level: count
        for level, count in db_session.execute(
            select(
                func.coalesce(GrammarPoint.level, VocabItem.level),
                func.count(Prompt.id),
            )
            .select_from(Prompt)
            .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
            .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
            .group_by(func.coalesce(GrammarPoint.level, VocabItem.level))
        ).all()
    }

    # Single query grouped by (level, status) gives both queue_counts and total_in_queue.
    status_level_rows = db_session.execute(
        select(
            func.coalesce(GrammarPoint.level, VocabItem.level),
            ReviewState.status,
            func.count(ReviewState.prompt_id),
        )
        .select_from(ReviewState)
        .join(Prompt, Prompt.id == ReviewState.prompt_id)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .where(ReviewState.user_id == user.id)
        .group_by(func.coalesce(GrammarPoint.level, VocabItem.level), ReviewState.status)
    ).all()

    queue_counts: dict = {}
    total_in_queue = 0
    for level, _status, count in status_level_rows:
        count = int(count)
        total_in_queue += count
        queue_counts[level] = queue_counts.get(level, 0) + count

    levels_data = []
    for level in CEFR_LEVELS:
        grammar_count = int(grammar_counts.get(level, 0))
        vocab_count = int(vocab_counts.get(level, 0))
        total_prompts = int(prompt_counts.get(level, 0))
        in_queue = int(queue_counts.get(level, 0))

        levels_data.append({
            "level": level,
            "grammar_points": grammar_count,
            "vocab_items": vocab_count,
            "total_prompts": total_prompts,
            "in_queue": in_queue,
            "fully_added": in_queue >= total_prompts and total_prompts > 0,
        })

    return {
        "levels": levels_data,
        "total_in_queue": total_in_queue,
        "preferences": {
            "daily_new_limit": user.daily_new_limit,
            "content_preference": user.content_preference,
            "selected_levels": _selected_levels(user),
        },
    }


def learn_count(db_session: Session, user: User, kind: str | None) -> dict:
    remaining = _learning_item_count(db_session, user, kind)
    return {"remaining": remaining}


def learn_queue(db_session: Session, user: User, limit: int, kind: str | None) -> dict:
    levels = _selected_levels(user)
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
    if levels:
        stmt = stmt.where(or_(GrammarPoint.level.in_(levels), VocabItem.level.in_(levels)))
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    stmt = stmt.order_by(Prompt.id.asc()).limit(limit)

    rows = db_session.execute(stmt).all()
    items = [prompt_to_dict(prompt, grammar_point, vocab_item) for (prompt, grammar_point, vocab_item) in rows]

    available_stmt = (
        select(func.count())
        .select_from(Prompt)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(ReviewState.prompt_id.is_(None))
    )
    if levels:
        available_stmt = available_stmt.where(or_(GrammarPoint.level.in_(levels), VocabItem.level.in_(levels)))
    if kind:
        available_stmt = available_stmt.where(Prompt.kind == kind)
    available_to_add = int(db_session.execute(available_stmt).scalar_one())

    new_in_queue = _learning_item_count(db_session, user, kind)

    return {
        "items": items,
        "remaining": available_to_add,
        "available_to_add": available_to_add,
        "new_in_queue": new_in_queue,
    }


def learn_next(
    db_session: Session,
    user: User,
    count: int,
    kind: str | None,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> dict:
    if count < 1:
        raise ServiceError(400, "count must be >= 1")
    if count > 50:
        raise ServiceError(400, "count too large")

    levels = _selected_levels(user)
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
    if levels:
        stmt = stmt.where(or_(GrammarPoint.level.in_(levels), VocabItem.level.in_(levels)))
    if kind:
        stmt = stmt.where(Prompt.kind == kind)
    stmt = stmt.order_by(Prompt.id.asc()).limit(count)

    rows = db_session.execute(stmt).all()
    now = now_utc()
    due_now = now.replace(tzinfo=None)
    local_today = local_date_from_utc(now, tz_offset, time_zone)

    added_items = []
    for (prompt, grammar_point, vocab_item) in rows:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now, local_today))
        added_items.append(prompt_to_dict(prompt, grammar_point, vocab_item))

    db_session.commit()

    remaining_stmt = (
        select(func.count())
        .select_from(Prompt)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .where(ReviewState.prompt_id.is_(None))
    )
    if levels:
        remaining_stmt = remaining_stmt.where(or_(GrammarPoint.level.in_(levels), VocabItem.level.in_(levels)))
    if kind:
        remaining_stmt = remaining_stmt.where(Prompt.kind == kind)
    remaining = int(db_session.execute(remaining_stmt).scalar_one())

    return LearnNextOut(added=added_items, remaining=remaining).model_dump()


def learn_add_grammar_point(
    db_session: Session,
    user: User,
    grammar_point_id: int,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> dict:
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
    now = now_utc()
    due_now = now.replace(tzinfo=None)
    local_today = local_date_from_utc(now, tz_offset, time_zone)

    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now, local_today))
        added_count += 1

    db_session.commit()
    return {
        "added": added_count,
        "grammar_point_id": grammar_point_id,
        "grammar_point_title": grammar_point.title,
    }


def learn_add_vocab_item(
    db_session: Session,
    user: User,
    vocab_item_id: int,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> dict:
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
    now = now_utc()
    due_now = now.replace(tzinfo=None)
    local_today = local_date_from_utc(now, tz_offset, time_zone)

    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now, local_today))
        added_count += 1

    db_session.commit()
    return {"added": added_count, "vocab_item_id": vocab_item_id, "vocab_word": vocab_item.word}


def learn_add_level(
    db_session: Session,
    user: User,
    level: str,
    kind: str | None,
    limit: int | None,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> dict:
    if level.upper() not in CEFR_LEVELS:
        raise ServiceError(400, f"Invalid level. Must be one of: {', '.join(CEFR_LEVELS)}")

    level = level.upper()
    limit = _daily_limit(user, limit)
    if kind not in [None, "grammar", "vocab"]:
        raise ServiceError(400, "Content kind must be 'grammar' or 'vocab'")

    user.daily_new_limit = limit
    if kind:
        user.content_preference = kind
    elif not user.content_preference:
        user.content_preference = "both"
    _add_selected_level(user, level)
    db_session.commit()

    result = auto_add_items(db_session, user, tz_offset, time_zone)
    result.update({
        "level": level,
        "kind": None if user.content_preference == "both" else user.content_preference,
        "daily_limit": limit,
        "unlocked": True,
    })
    return result


def learn_remove_level(db_session: Session, user: User, level: str) -> dict:
    if level.upper() not in CEFR_LEVELS:
        raise ServiceError(400, f"Invalid level. Must be one of: {', '.join(CEFR_LEVELS)}")

    level = level.upper()
    _remove_selected_level(user, level)

    level_prompt_ids = (
        select(Prompt.id)
        .outerjoin(GrammarPoint, GrammarPoint.id == Prompt.grammar_point_id)
        .outerjoin(VocabItem, VocabItem.id == Prompt.vocab_item_id)
        .where(or_(GrammarPoint.level == level, VocabItem.level == level))
    )
    result = db_session.execute(
        delete(ReviewState)
        .where(
            and_(
                ReviewState.user_id == user.id,
                ReviewState.status == "learning",
                ReviewState.prompt_id.in_(level_prompt_ids),
            )
        )
        .execution_options(synchronize_session=False)
    )

    db_session.commit()
    return {
        "level": level,
        "unlocked": False,
        "removed_learning_items": int(result.rowcount or 0),
        "selected_levels": _selected_levels(user),
    }


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

    # Batch-fetch all grammar examples in one query instead of one per grammar point.
    grammar_point_ids = list(dict.fromkeys(
        gp.id for _, p, gp, _ in rows if p.kind == "grammar" and gp
    ))
    examples_by_gp: dict[int, list] = {}
    if grammar_point_ids:
        for ex in db_session.execute(
            select(GrammarExample)
            .where(GrammarExample.grammar_point_id.in_(grammar_point_ids))
            .order_by(GrammarExample.sort_order)
        ).scalars().all():
            examples_by_gp.setdefault(ex.grammar_point_id, []).append(ex)

    seen_grammar: set[int] = set()
    seen_vocab: set[int] = set()
    items: list[dict] = []

    for (_unused_review_state, prompt, grammar_point, vocab_item) in rows:
        if prompt.kind == "grammar" and grammar_point:
            if grammar_point.id in seen_grammar:
                continue
            seen_grammar.add(grammar_point.id)

            examples = examples_by_gp.get(grammar_point.id, [])

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


def mark_items_studied(db_session: Session, user: User) -> dict:
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


def auto_add_items(
    db_session: Session,
    user: User,
    tz_offset: int | None,
    time_zone: str | None = None,
) -> dict:
    if not user.daily_new_limit or not user.selected_levels:
        raise ServiceError(
            400,
            "No learning preferences set. Please configure your daily goal first.",
        )

    now = now_utc()
    local_today = local_date_from_utc(now, tz_offset, time_zone)

    unstudied_count = _learning_item_count(db_session, user)

    if unstudied_count > 0:
        return {
            "added": 0,
            "message": f"You still have {unstudied_count} unstudied items. Complete them before getting new items.",
            "unstudied_count": unstudied_count,
        }

    levels = _selected_levels(user)
    today_count = _introduced_today_count(db_session, user, local_today)

    if user.last_items_added_at and today_count == 0:
        last_added_local = local_date_from_utc(
            user.last_items_added_at,
            tz_offset,
            time_zone,
        )
        if last_added_local >= local_today:
            return {
                "added": 0,
                "message": "New items already added today. Come back tomorrow!",
                "already_added_today": True,
                "daily_limit": user.daily_new_limit,
                "introduced_today": today_count,
            }

    remaining_today = max(user.daily_new_limit - today_count, 0)

    if remaining_today <= 0:
        return {
            "added": 0,
            "message": "New items already added today. Come back tomorrow!",
            "already_added_today": True,
            "daily_limit": user.daily_new_limit,
            "introduced_today": today_count,
        }

    kind = None if user.content_preference == "both" else user.content_preference

    if kind is None:
        grammar_limit = (remaining_today + 1) // 2
        grammar_prompts = _select_unseen_prompts(
            db_session,
            user,
            levels,
            grammar_limit,
            kind="grammar",
        )
        vocab_limit = remaining_today - len(grammar_prompts)
        selected_prompt_ids = {prompt.id for prompt in grammar_prompts}
        vocab_prompts = _select_unseen_prompts(
            db_session,
            user,
            levels,
            vocab_limit,
            kind="vocab",
            exclude_prompt_ids=selected_prompt_ids,
        )
        prompts = list(grammar_prompts) + list(vocab_prompts)

        backfill_limit = remaining_today - len(prompts)
        if backfill_limit > 0:
            selected_prompt_ids = {prompt.id for prompt in prompts}
            prompts.extend(_select_unseen_prompts(
                db_session,
                user,
                levels,
                backfill_limit,
                exclude_prompt_ids=selected_prompt_ids,
            ))
    else:
        prompts = _select_unseen_prompts(db_session, user, levels, remaining_today, kind=kind)

    due_now = now.replace(tzinfo=None)
    added_count = 0
    for prompt in prompts:
        db_session.add(_new_learning_state(user.id, prompt.id, due_now, local_today))
        added_count += 1

    if added_count > 0:
        user.last_items_added_at = due_now

    db_session.commit()

    return {
        "added": added_count,
        "message": f"Added {added_count} new items to your queue" if added_count > 0 else "No new items available",
        "daily_limit": user.daily_new_limit,
        "introduced_today": today_count + added_count,
    }
