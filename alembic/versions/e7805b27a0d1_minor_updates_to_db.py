"""minor updates to db

Revision ID: e7805b27a0d1
Revises: 7743a58992f6
Create Date: 2025-05-25 00:22:09.711106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7805b27a0d1'
down_revision: Union[str, None] = '7743a58992f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
