"""add soft delete columns to patients

Revision ID: b2f1a7c4d9e0
Revises: fded53d3c0af
Create Date: 2026-07-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f1a7c4d9e0'
down_revision: Union[str, Sequence[str], None] = 'fded53d3c0af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'patients',
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'patients',
        sa.Column(
            'is_deleted',
            sa.Boolean(),
            server_default=sa.text('0'),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('patients', 'is_deleted')
    op.drop_column('patients', 'deleted_at')
