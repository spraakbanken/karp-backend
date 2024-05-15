"""add api_keys table

Revision ID: b8af4498c011
Revises: 47405b5dfdb6
Create Date: 2024-05-10 14:43:28.628683

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8af4498c011"
down_revision = "47405b5dfdb6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_key", sa.String(length=36), nullable=False, unique=True),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    pass
