"""remove repo_id field from history tables

Revision ID: 772761d11c7c
Revises: 12fba3f461b2
Create Date: 2024-01-30 16:53:31.063354

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "772761d11c7c"
down_revision = "12fba3f461b2"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    for resource_id, entry_repo_id in conn.execute(
        text("select distinct resource_id, entry_repo_id from resources")
    ):
        table_name = f"{resource_id}_{entry_repo_id[-16:]}"
        op.drop_column(table_name, "repo_id")
