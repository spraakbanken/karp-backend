"""remove resource_type column from resources

Revision ID: 1022e239ee16
Revises: 191c2e9d0906
Create Date: 2024-11-11 11:34:58.727019

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1022e239ee16"
down_revision = "191c2e9d0906"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("resources", "resource_type")
