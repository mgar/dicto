"""add review_state hot path index

Revision ID: 2f1b7e2d8c8c
Revises: ba53d719e878
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2f1b7e2d8c8c"
down_revision: Union[str, None] = "ba53d719e878"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_review_state_user_status_due",
        "review_state",
        ["user_id", "status", "due_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_state_user_status_due", table_name="review_state")