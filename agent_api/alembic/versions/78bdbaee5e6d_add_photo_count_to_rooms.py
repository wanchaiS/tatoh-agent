"""add photo_count to rooms

Revision ID: 78bdbaee5e6d
Revises: d621e2cda7cb
Create Date: 2026-03-12 00:14:43.387989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '78bdbaee5e6d'
down_revision: Union[str, Sequence[str], None] = 'd621e2cda7cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('rooms', sa.Column('photo_count', sa.Integer(), server_default='0', nullable=False), schema='tatoh')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rooms', 'photo_count', schema='tatoh')
