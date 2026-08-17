"""add visitors

Revision ID: 16346f3d920b
Revises: f6488de6a875
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "16346f3d920b"
down_revision: Union[str, None] = "f6488de6a875"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visitors",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visitors_last_seen", "visitors", ["last_seen"])


def downgrade() -> None:
    op.drop_index("ix_visitors_last_seen", table_name="visitors")
    op.drop_table("visitors")
