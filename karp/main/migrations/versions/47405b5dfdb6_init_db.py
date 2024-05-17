"""init db

Revision ID: 5bb29472d33f
Revises:
Create Date: ~2018-12-12 13:48:19.255822~2024-03-05

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_json import NestedMutableJson

from karp.db_infrastructure.types import ULIDType

# revision identifiers, used by Alembic.
revision = "47405b5dfdb6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resources",
        sa.Column("history_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", ULIDType, nullable=False),
        sa.Column("resource_id", sa.String(length=32), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("table_name", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("config", NestedMutableJson, nullable=False),
        sa.Column("is_published", sa.Boolean, index=True, nullable=True, default=None),
        sa.Column("last_modified", sa.Float(precision=53), nullable=False),
        sa.Column("last_modified_by", sa.String(100), nullable=False),
        sa.Column("message", sa.String(100), nullable=False),
        sa.Column("op", sa.Enum("ADDED", "UPDATED", "DELETED"), nullable=False),
        sa.Column("discarded", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("history_id"),
        sa.UniqueConstraint("entity_id", "version", name="entity_id_version_unique_constraint"),
        sa.UniqueConstraint(
            "table_name", "version", name="table_name_version_unique_constraint"
        ),
    )


def downgrade():
    pass
