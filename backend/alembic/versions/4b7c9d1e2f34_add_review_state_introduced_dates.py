"""add review_state introduced dates

Revision ID: 4b7c9d1e2f34
Revises: 2f1b7e2d8c8c
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b7c9d1e2f34"
down_revision: Union[str, None] = "2f1b7e2d8c8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("review_state", sa.Column("introduced_at", sa.DateTime(), nullable=True))
    op.add_column("review_state", sa.Column("introduced_local_date", sa.Date(), nullable=True))

    op.execute(
        """
        UPDATE review_state rs
        SET
          introduced_at = COALESCE(
            (
              SELECT MIN(rl.answered_at)
              FROM review_log rl
              WHERE rl.user_id = rs.user_id
                AND rl.prompt_id = rs.prompt_id
            ),
            rs.due_at
          ),
          introduced_local_date = COALESCE(
            (
              SELECT MIN(rl.local_date)
              FROM review_log rl
              WHERE rl.user_id = rs.user_id
                AND rl.prompt_id = rs.prompt_id
                AND rl.local_date IS NOT NULL
            ),
            DATE(rs.due_at)
          )
        """
    )

    op.create_index(
        "ix_review_state_user_introduced_local_date",
        "review_state",
        ["user_id", "introduced_local_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_state_user_introduced_local_date", table_name="review_state")
    op.drop_column("review_state", "introduced_local_date")
    op.drop_column("review_state", "introduced_at")
