"""entry_repo_id -> table_name

Revision ID: e09588a7e6ca
Revises: 772761d11c7c
Create Date: 2024-01-30 17:31:48.508669

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e09588a7e6ca"
down_revision = "772761d11c7c"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    op.add_column("resources", sa.Column("table_name", sa.Text(), nullable=False))
    # table_name is {resource_id}_{entry_repo_id[-16:]}
    conn.execute(
        sa.text(
            """
    update resources set
    table_name=concat(resource_id, "_", right(entry_repo_id, 16))
    """
        )
    )
    op.create_unique_constraint(
        "table_name_version_unique_constraint", "resources", ["table_name", "version"]
    )
    op.drop_column("resources", "entry_repo_id")
