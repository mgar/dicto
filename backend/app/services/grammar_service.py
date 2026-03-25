"""Grammar points listing and detail (learner-facing)."""
import json

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.dependencies import now_utc
from app.models import GrammarExample, GrammarPoint, Prompt, ReviewState, User
from app.services.errors import ServiceError
from app.utils import mastery_summary


def list_grammar_points(db_session: Session) -> dict:
    rows = db_session.execute(
        select(GrammarPoint).order_by(GrammarPoint.level, GrammarPoint.id)
    ).scalars().all()
    return {
        "items": [
            {
                "id": grammar_point.id,
                "level": grammar_point.level,
                "slug": grammar_point.slug,
                "title": grammar_point.title,
                "short_description": grammar_point.short_description,
            }
            for grammar_point in rows
        ]
    }


def list_grammar_points_by_level(db_session: Session, user: User) -> dict:
    grammar_points = db_session.execute(
        select(GrammarPoint).order_by(GrammarPoint.level, GrammarPoint.id)
    ).scalars().all()
    result: dict = {}
    for grammar_point in grammar_points:
        total_prompts = db_session.execute(
            select(func.count()).select_from(Prompt).where(Prompt.grammar_point_id == grammar_point.id)
        ).scalar_one()

        in_queue = db_session.execute(
            select(func.count())
            .select_from(ReviewState)
            .join(Prompt, Prompt.id == ReviewState.prompt_id)
            .where(
                and_(
                    ReviewState.user_id == user.id,
                    Prompt.grammar_point_id == grammar_point.id,
                )
            )
        ).scalar_one()

        level = grammar_point.level
        if level not in result:
            result[level] = {"level": level, "items": [], "total_prompts": 0, "in_queue": 0}

        result[level]["items"].append({
            "id": grammar_point.id,
            "slug": grammar_point.slug,
            "title": grammar_point.title,
            "short_description": grammar_point.short_description,
            "total_prompts": total_prompts,
            "in_queue": in_queue,
            "fully_added": in_queue >= total_prompts and total_prompts > 0,
        })
        result[level]["total_prompts"] += total_prompts
        result[level]["in_queue"] += in_queue

    levels_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    sorted_result = [result[level] for level in levels_order if level in result]
    return {"levels": sorted_result}


def get_grammar_point(db_session: Session, user: User, grammar_point_id: int) -> dict:
    grammar_point = db_session.execute(
        select(GrammarPoint).where(GrammarPoint.id == grammar_point_id)
    ).scalar_one_or_none()
    if not grammar_point:
        raise ServiceError(404, "Not found")

    examples = db_session.execute(
        select(GrammarExample)
        .where(GrammarExample.grammar_point_id == grammar_point_id)
        .order_by(GrammarExample.sort_order)
    ).scalars().all()

    structure: list = []
    if grammar_point.structure:
        try:
            structure = json.loads(grammar_point.structure)
        except json.JSONDecodeError:
            structure = []

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
        .where(Prompt.grammar_point_id == grammar_point_id)
    ).one()

    return {
        "id": grammar_point.id,
        "level": grammar_point.level,
        "slug": grammar_point.slug,
        "title": grammar_point.title,
        "short_description": grammar_point.short_description,
        "structure": structure,
        "explanation": grammar_point.explanation,
        "examples": [
            {
                "id": example.id,
                "sentence": example.sentence,
                "translation": example.translation,
                "highlight": example.highlight,
                "notes": example.notes,
            }
            for example in examples
        ],
        "mastery": mastery_summary(
            total_prompts=int(mastery_row.total_prompts or 0),
            reviewed_prompts=int(mastery_row.reviewed_prompts or 0),
            avg_interval_days=float(mastery_row.avg_interval_days or 0.0),
            due_now=int(mastery_row.due_now or 0),
        ),
    }
