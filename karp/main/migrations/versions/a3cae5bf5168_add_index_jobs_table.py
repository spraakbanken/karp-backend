"""add index jobs table

Revision ID: a3cae5bf5168
Revises: 1022e239ee16
Create Date: 2024-11-15 12:04:43.232850

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

import karp

# revision identifiers, used by Alembic.
revision = "a3cae5bf5168"
down_revision = "1022e239ee16"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "index_job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource_id", sa.String(length=32), nullable=False),
        sa.Column("op", sa.Enum("ADD", "DELETE", "REINDEX"), nullable=False),
        sa.Column("entry_id", karp.db_infrastructure.types.ulid.ULIDType(length=26), nullable=True),
        sa.Column("body", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
