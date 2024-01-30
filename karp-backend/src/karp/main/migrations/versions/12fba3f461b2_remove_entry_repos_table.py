"""remove entry_repos table

Revision ID: 12fba3f461b2
Revises: c9a01aaad322
Create Date: 2024-01-30 15:19:35.963876

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '12fba3f461b2'
down_revision = 'c9a01aaad322'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('entry_repos')
