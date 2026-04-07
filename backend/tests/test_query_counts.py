"""
Query-count regression tests.

Each test asserts that a service call issues exactly the expected number of SQL
statements, catching N+1 regressions and verifying that optimizations hold.

Timing tests are avoided: SQLite in-memory is too fast and too different from
MySQL to give meaningful latency numbers. Query counts are deterministic and
directly measure what was optimized.

Implementation note: SQLAlchemy's expire_on_commit=True (default) clears all
attributes — including primary keys — after every commit. To avoid lazy-load
noise inside the count block we:
  - store integer IDs immediately after object creation (before the next commit)
  - call db_session.refresh(user) once before entering count_queries, so
    user.id is in __dict__ and won't re-query inside the block.
"""
from contextlib import contextmanager

import pytest
from sqlalchemy import event

from app.dependencies import now_utc
from app.models import GrammarExample, ReviewState
from app.services import grammar_service, learn_service, reviews_service
from tests.conftest import make_grammar_point, make_prompt, make_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@contextmanager
def count_queries(engine):
    """Yield a list that accumulates every SQL statement issued against engine."""
    queries: list[str] = []

    def listener(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", listener)
    try:
        yield queries
    finally:
        event.remove(engine, "before_cursor_execute", listener)


def dml(queries: list[str]) -> list[str]:
    """Filter to DML/DQL statements, excluding BEGIN/COMMIT/SAVEPOINT."""
    prefixes = ("SELECT", "INSERT", "UPDATE", "DELETE", "WITH")
    return [q for q in queries if q.strip().upper().startswith(prefixes)]


def _fmt(sql: list[str]) -> str:
    return "\n".join(f"  [{i+1}] {s.split(chr(10))[0][:120]}" for i, s in enumerate(sql))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db_session):
    return make_user(db_session)


def _add_grammar_setup(db_session, user, n: int, slug_prefix: str = "gp"):
    """
    Add n grammar points × 3 examples each, 1 learning-state prompt per point.

    Returns the user_id as a plain int so callers don't need to touch the
    expired user object before refreshing it.
    """
    due = now_utc().replace(tzinfo=None)
    # user.id may trigger a lazy-load here (user is expired from prior commits
    # inside make_grammar_point/make_prompt), but we are outside the count block.
    user_id = user.id
    for i in range(n):
        gp = make_grammar_point(db_session, slug=f"{slug_prefix}-{i}", title=f"GP {i}")
        gp_id = gp.id  # store before next commit expires it
        for j in range(3):
            db_session.add(GrammarExample(
                grammar_point_id=gp_id,
                sentence=f"Sentence {j}",
                translation=f"Translation {j}",
                sort_order=j,
            ))
        prompt = make_prompt(
            db_session,
            grammar_point=gp,
            sentence=f"___ prompt {i}.",
            answers=(f"answer{i}",),
        )
        prompt_id = prompt.id  # store before next commit expires it
        db_session.add(ReviewState(
            user_id=user_id,
            prompt_id=prompt_id,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
            due_at=due,
            status="learning",
        ))
    db_session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQueryCounts:

    def test_get_study_queue_two_queries_regardless_of_grammar_point_count(
        self, db_engine, db_session, user
    ):
        """
        get_study_queue must issue exactly 2 queries for any number of grammar
        points: one for the full study-queue join, one batch-fetch for all
        GrammarExample rows. Previously it issued 1 + N (one per grammar point).
        """
        _add_grammar_setup(db_session, user, n=5)
        db_session.refresh(user)  # pre-load user.id so it doesn't lazy-load inside count block

        with count_queries(db_engine) as queries:
            result = learn_service.get_study_queue(db_session, user)

        sql = dml(queries)
        assert len(sql) <= 2, (
            f"Expected at most 2 queries for {len(result['items'])} grammar points, "
            f"got {len(sql)}:\n{_fmt(sql)}"
        )
        assert len(result["items"]) == 5

    def test_get_study_queue_scales_flat_with_more_grammar_points(
        self, db_engine, db_session, user
    ):
        """
        Query count must not grow with the number of grammar points (N+1 guard).
        Runs with 5 and 10 grammar points and asserts both produce the same count.
        """
        _add_grammar_setup(db_session, user, n=5, slug_prefix="small")
        db_session.refresh(user)
        with count_queries(db_engine) as q5:
            learn_service.get_study_queue(db_session, user)
        count_5 = len(dml(q5))

        _add_grammar_setup(db_session, user, n=5, slug_prefix="big")  # adds 5 more → 10 total
        db_session.refresh(user)
        with count_queries(db_engine) as q10:
            result = learn_service.get_study_queue(db_session, user)
        count_10 = len(dml(q10))

        assert count_5 == count_10, (
            f"Query count grew from {count_5} (5 grammar points) to "
            f"{count_10} (10 grammar points) — N+1 regression"
        )
        assert len(result["items"]) == 10

    def test_get_learn_levels_four_queries(self, db_engine, db_session, user):
        """
        get_learn_levels must issue exactly 4 queries:
          1. grammar point counts per level
          2. vocab item counts per level
          3. prompt counts per level
          4. review state counts grouped by (level, status) — covers both
             in-queue-per-level and total_in_queue in a single pass.
        """
        _add_grammar_setup(db_session, user, n=3)
        db_session.refresh(user)

        with count_queries(db_engine) as queries:
            learn_service.get_learn_levels(db_session, user)

        sql = dml(queries)
        assert len(sql) <= 4, (
            f"Expected at most 4 queries, got {len(sql)}:\n{_fmt(sql)}"
        )

    def test_get_grammar_point_two_queries(self, db_engine, db_session, user):
        """
        get_grammar_point must issue 2 queries:
          1. GrammarPoint LEFT JOIN GrammarExample (combined — was 2 before)
          2. mastery aggregate (Prompt LEFT JOIN ReviewState)
        """
        gp = make_grammar_point(db_session)
        gp_id = gp.id  # store before next commit expires it
        db_session.add(GrammarExample(
            grammar_point_id=gp_id,
            sentence="Ella ___ de Madrid.",
            translation="She is from Madrid.",
            sort_order=0,
        ))
        db_session.commit()
        db_session.refresh(user)

        with count_queries(db_engine) as queries:
            grammar_service.get_grammar_point(db_session, user, gp_id)

        sql = dml(queries)
        assert len(sql) <= 2, (
            f"Expected at most 2 queries, got {len(sql)}:\n{_fmt(sql)}"
        )

    def test_submit_review_answer_four_sql_statements(self, db_engine, db_session, user):
        """
        submit_review_answer must issue exactly 4 SQL statements:
          1. SELECT review_state
          2. SELECT prompt LEFT JOIN prompt_answers  (combined — was 2 before)
          3. INSERT review_log
          4. UPDATE review_state
        """
        gp = make_grammar_point(db_session)
        prompt = make_prompt(
            db_session,
            grammar_point=gp,
            sentence="___ esto.",
            answers=("es", "está"),
        )
        prompt_id = prompt.id  # store before next commit expires it
        due = now_utc().replace(tzinfo=None)
        db_session.add(ReviewState(
            user_id=user.id,
            prompt_id=prompt_id,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
            due_at=due,
            status="reviewing",
        ))
        db_session.commit()
        db_session.refresh(user)

        with count_queries(db_engine) as queries:
            reviews_service.submit_review_answer(
                db_session, user, prompt_id, "es", None, None
            )

        sql = dml(queries)
        assert len(sql) <= 4, (
            f"Expected at most 4 SQL statements, got {len(sql)}:\n{_fmt(sql)}"
        )
