"""use ulid as str

Revision ID: c9a01aaad322
Revises: d2f8d1c19b65
Create Date: 2022-12-01 12:36:55.684153

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType
from karp.db_infrastructure.types import ULIDType


# revision identifiers, used by Alembic.
revision = "c9a01aaad322"
down_revision = "d2f8d1c19b65"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("resources", "entity_id", nullable=False, type_=ULIDType)
    op.alter_column("resources", "entry_repo_id", nullable=False, type_=ULIDType)
    op.alter_column("entry_repos", "entity_id", nullable=False, type_=ULIDType)


def downgrade():
    op.alter_column("resources", "entity_id", nullable=False, type_=UUIDType)
    op.alter_column("resources", "entry_repo_id", nullable=False, type_=UUIDType)
    op.alter_column("entry_repos", "entity_id", nullable=False, type_=UUIDType)
