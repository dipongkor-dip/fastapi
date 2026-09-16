"""add phone of users table

Revision ID: d15e04d30ad7
Revises: f125e03b3280
Create Date: 2026-09-16 19:39:13.451370

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d15e04d30ad7"
down_revision: Union[str, Sequence[str], None] = "f125e03b3280"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass
