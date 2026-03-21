"""add_last_items_added_at_to_users

Revision ID: ba53d719e878
Revises: a3bad98e4c87
Create Date: 2026-03-20 03:33:04.805943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba53d719e878'
down_revision: Union[str, None] = 'a3bad98e4c87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_items_added_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_items_added_at")
