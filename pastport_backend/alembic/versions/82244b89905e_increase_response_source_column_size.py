"""increase_response_source_column_size

Revision ID: 82244b89905e
Revises: d83279cf7a3a
Create Date: 2025-09-30 19:46:14.336842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82244b89905e'
down_revision: Union[str, Sequence[str], None] = 'd83279cf7a3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase response_source column size from 20 to 50 characters
    op.alter_column('chat_messages', 'response_source',
                   existing_type=sa.String(length=20),
                   type_=sa.String(length=50),
                   existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    pass
