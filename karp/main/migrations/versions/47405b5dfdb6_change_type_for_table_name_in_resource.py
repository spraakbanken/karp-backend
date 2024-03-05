"""change type for table_name in resource

Revision ID: 47405b5dfdb6
Revises: 44229cf4d74b
Create Date: 2024-03-04 20:07:05.753382

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "47405b5dfdb6"
down_revision = "44229cf4d74b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "resources",
        "table_name",
        existing_type=mysql.TEXT(),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade():
    pass
