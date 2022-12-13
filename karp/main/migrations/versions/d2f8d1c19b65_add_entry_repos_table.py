"""add entry_repos table

Revision ID: d2f8d1c19b65
Revises: 5bb29472d33f
Create Date: 2021-10-27 22:08:06.924305

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType
from sqlalchemy_json import NestedMutableJson


# revision identifiers, used by Alembic.
revision = "d2f8d1c19b65"
down_revision = "5bb29472d33f"
branch_labels = None
depends_on = None


def create_entry_repos():
    op.create_table(
        "entry_repos",
        sa.Column("history_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("connection_str", sa.String(length=128)),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("config", NestedMutableJson, nullable=False),
        sa.Column("last_modified", sa.Float(precision=53), nullable=False),
        sa.Column("last_modified_by", sa.String(100), nullable=False),
        sa.Column("message", sa.String(100), nullable=False),
        sa.Column("discarded", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("history_id"),
    )


def upgrade():
    create_entry_repos()


def downgrade():
    op.drop_table("entry_repos")
