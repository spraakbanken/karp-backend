"""init db

Revision ID: 5bb29472d33f
Revises:
Create Date: 2018-12-12 13:48:19.255822

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType
from sqlalchemy_json import NestedMutableJson

# revision identifiers, used by Alembic.
revision = "5bb29472d33f"
down_revision = None
branch_labels = None
depends_on = None


def create_resources():
    op.create_table(
        "resources",
        sa.Column("history_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", UUIDType, nullable=False),
        sa.Column("resource_id", sa.String(length=32), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("entry_repo_id", UUIDType),
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
        sa.UniqueConstraint(
            "entity_id", "version", name="entity_id_version_unique_constraint"
        ),
    )


def upgrade():
    create_resources()
    # op.create_table(
    #     "dummy_entry",
    #     sa.Column("id", sa.Integer(), nullable=False),
    #     sa.Column("body", sa.Text(), nullable=False),
    #     sa.Column("deleted", sa.Boolean(), nullable=True),
    #     sa.Column("entry_id", sa.String(length=30), nullable=False),
    #     sa.PrimaryKeyConstraint("id"),
    #     sa.UniqueConstraint("entry_id", name="entry_id_unique_constraint"),
    # )
    # op.create_table(
    #     "dummy_history",
    #     sa.Column("id", sa.Integer(), nullable=False),
    #     sa.Column("entry_id", sa.Integer(), nullable=False),
    #     sa.Column("user_id", sa.Text(), nullable=False),
    #     sa.Column(
    #         "timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False
    #     ),
    #     sa.Column("body", sa.Text(), nullable=True),
    #     sa.Column("op", sa.Enum("ADD", "DELETE", "UPDATE"), nullable=False),
    #     sa.Column("version", sa.Integer(), nullable=False),
    #     sa.Column("message", sa.Text(), nullable=True),
    #     sa.PrimaryKeyConstraint("id"),
    #     sa.UniqueConstraint(
    #         "entry_id", "version", name="entry_id_version_unique_constraint"
    #     ),
    # )


def downgrade():
    op.drop_table("resources")
    # op.drop_table("dummy_history")
    # op.drop_table("dummy_entry")
