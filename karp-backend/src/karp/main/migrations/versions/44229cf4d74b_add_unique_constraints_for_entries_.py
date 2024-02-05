"""Add unique constraints for entries tables.

Revision ID: 44229cf4d74b
Revises: e09588a7e6ca
Create Date: 2024-02-05 11:29:56.613345

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "44229cf4d74b"
down_revision = "e09588a7e6ca"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    for (table_name,) in conn.execute(
        sa.text("select distinct table_name from resources")
    ):
        op.execute(
            f"alter table {table_name} drop constraint if exists id_version_unique_constraint"
        )
        op.create_unique_constraint(
            "id_version_unique_constraint", table_name, ["entity_id", "version"]
        )
