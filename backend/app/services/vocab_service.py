"""Vocabulary listing and detail (learner-facing)."""
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import Prompt, ReviewState, User, VocabItem
from app.services.errors import ServiceError
from app.utils import mastery_summary

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def list_vocab_items_by_level(db_session: Session, user: User) -> dict:
    rows = db_session.execute(
        select(
            VocabItem.id,
            VocabItem.level,
            VocabItem.word,
            VocabItem.translation,
            VocabItem.part_of_speech,
            VocabItem.gender,
            func.count(Prompt.id).label("total_prompts"),
            func.sum(case((ReviewState.user_id.is_not(None), 1), else_=0)).label("in_queue"),
        )
        .select_from(VocabItem)
        .outerjoin(Prompt, Prompt.vocab_item_id == VocabItem.id)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .group_by(
            VocabItem.id,
            VocabItem.level,
            VocabItem.word,
            VocabItem.translation,
            VocabItem.part_of_speech,
            VocabItem.gender,
        )
        .order_by(VocabItem.level, VocabItem.word)
    ).all()
    result: dict = {}
    for row in rows:
        total_prompts = int(row.total_prompts or 0)
        in_queue = int(row.in_queue or 0)
        level = row.level
        if level not in result:
            result[level] = {"level": level, "items": [], "total_prompts": 0, "in_queue": 0}

        result[level]["items"].append({
            "id": row.id,
            "word": row.word,
            "translation": row.translation,
            "part_of_speech": row.part_of_speech,
            "gender": row.gender,
            "total_prompts": total_prompts,
            "in_queue": in_queue,
            "fully_added": in_queue >= total_prompts and total_prompts > 0,
        })
        result[level]["total_prompts"] += total_prompts
        result[level]["in_queue"] += in_queue

    for level_data in result.values():
        level_data["fully_added"] = (
            level_data["in_queue"] >= level_data["total_prompts"]
            and level_data["total_prompts"] > 0
        )

    sorted_levels = sorted(
        result.values(),
        key=lambda level_row: CEFR_ORDER.index(level_row["level"])
        if level_row["level"] in CEFR_ORDER
        else 99,
    )
    return {"levels": sorted_levels}


def list_vocab_items(db_session: Session, level: str | None, tag: str | None) -> dict:
    stmt = select(VocabItem).order_by(VocabItem.level, VocabItem.word)
    if level:
        stmt = stmt.where(VocabItem.level == level)
    if tag:
        stmt = stmt.where(VocabItem.tags.contains(tag))

    rows = db_session.execute(stmt).scalars().all()
    return {
        "items": [
            {
                "id": vocab_item.id,
                "level": vocab_item.level,
                "word": vocab_item.word,
                "translation": vocab_item.translation,
                "part_of_speech": vocab_item.part_of_speech,
                "gender": vocab_item.gender,
                "example_sentence": vocab_item.example_sentence,
                "example_translation": vocab_item.example_translation,
                "tags": vocab_item.tags,
            }
            for vocab_item in rows
        ]
    }


def get_vocab_item(db_session: Session, user: User, vocab_item_id: int) -> dict:
    vocab_item = db_session.execute(
        select(VocabItem).where(VocabItem.id == vocab_item_id)
    ).scalar_one_or_none()
    if not vocab_item:
        raise ServiceError(404, "Not found")

    due_now = now_utc().replace(tzinfo=None)
    mastery_row = db_session.execute(
        select(
            func.count(Prompt.id).label("total_prompts"),
            func.sum(case((ReviewState.prompt_id.is_not(None), 1), else_=0)).label("reviewed_prompts"),
            func.avg(func.coalesce(ReviewState.interval_days, 0)).label("avg_interval_days"),
            func.sum(
                case(
                    (
                        and_(
                            ReviewState.prompt_id.is_not(None),
                            ReviewState.status == "reviewing",
                            ReviewState.due_at <= due_now,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("due_now"),
        )
        .select_from(Prompt)
        .outerjoin(
            ReviewState,
            and_(
                ReviewState.prompt_id == Prompt.id,
                ReviewState.user_id == user.id,
            ),
        )
        .where(Prompt.vocab_item_id == vocab_item_id)
    ).one()

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
        "mastery": mastery_summary(
            total_prompts=int(mastery_row.total_prompts or 0),
            reviewed_prompts=int(mastery_row.reviewed_prompts or 0),
            avg_interval_days=float(mastery_row.avg_interval_days or 0.0),
            due_now=int(mastery_row.due_now or 0),
        ),
    }
