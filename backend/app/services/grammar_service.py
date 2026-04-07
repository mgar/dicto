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
    rows = db_session.execute(
        select(
            GrammarPoint.id,
            GrammarPoint.level,
            GrammarPoint.slug,
            GrammarPoint.title,
            GrammarPoint.short_description,
            func.count(Prompt.id).label("total_prompts"),
            func.sum(case((ReviewState.user_id.is_not(None), 1), else_=0)).label("in_queue"),
        )
        .select_from(GrammarPoint)
        .outerjoin(Prompt, Prompt.grammar_point_id == GrammarPoint.id)
        .outerjoin(
            ReviewState,
            and_(ReviewState.user_id == user.id, ReviewState.prompt_id == Prompt.id),
        )
        .group_by(
            GrammarPoint.id,
            GrammarPoint.level,
            GrammarPoint.slug,
            GrammarPoint.title,
            GrammarPoint.short_description,
        )
        .order_by(GrammarPoint.level, GrammarPoint.id)
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
            "slug": row.slug,
            "title": row.title,
            "short_description": row.short_description,
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
    gp_rows = db_session.execute(
        select(GrammarPoint, GrammarExample)
        .outerjoin(GrammarExample, GrammarExample.grammar_point_id == GrammarPoint.id)
        .where(GrammarPoint.id == grammar_point_id)
        .order_by(GrammarExample.sort_order)
    ).all()
    if not gp_rows:
        raise ServiceError(404, "Not found")
    grammar_point = gp_rows[0][0]
    examples = [row[1] for row in gp_rows if row[1] is not None]

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
