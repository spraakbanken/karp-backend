"""Support YAML in resource config.
Previously there was a constraint on resource.config to be valid JSON.

Revision ID: 191c2e9d0906
Revises: b8af4498c011
Create Date: 2024-06-11 18:27:21.930015

"""

from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "191c2e9d0906"
down_revision = "b8af4498c011"
branch_labels = None
depends_on = None


def upgrade():
    # This causes the column to be recreated without the valid JSON constraint
    op.alter_column("resources", "config", type_=mysql.LONGTEXT, nullable=False)
