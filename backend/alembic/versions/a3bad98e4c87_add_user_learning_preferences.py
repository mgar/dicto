"""add_user_learning_preferences

Revision ID: a3bad98e4c87
Revises: 9d3f2ac8134e
Create Date: 2026-03-20 03:28:22.030172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3bad98e4c87'
down_revision: Union[str, None] = '9d3f2ac8134e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("daily_new_limit", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("content_preference", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("selected_levels", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "selected_levels")
    op.drop_column("users", "content_preference")
    op.drop_column("users", "daily_new_limit")
