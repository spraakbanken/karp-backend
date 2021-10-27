"""add entry_repo_id column

Revision ID: fcafe9c1edbd
Revises: 5bb29472d33f
Create Date: 2021-10-27 12:26:30.946970

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType


# revision identifiers, used by Alembic.
revision = 'fcafe9c1edbd'
down_revision = '5bb29472d33f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('resources', sa.Column('entry_repo_id', UUIDType))


def downgrade():
    op.drop_column('resources', 'entry_repo_id')
