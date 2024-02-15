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

# Set this to True to remove the duplicate entries from the database,
# but maybe best to make a backup just in case :)
delete_duplicate_entries = False

def upgrade():
    conn = op.get_bind()
    for (table_name,) in conn.execute(sa.text("select distinct table_name from resources")):
        if delete_duplicate_entries:
            # Some tables have duplicate entries, which have the same
            # entity_id and version (but a different history_id).
            # In fact every field apart from history_id is the same,
            # so we can safely remove the duplicates.

            # Entries are considered duplicates if all fields apart
            # from history_id are the same
            columns_list = list(conn.execute(sa.text(f"select * from {table_name} limit 1")).keys())
            columns_list.remove('history_id')
            columns = ", ".join(columns_list)

            # When we have duplicates, we keep only the one with the
            # highest history_id. This query finds the entries we want
            # to keep (including non-duplicates).
            history_ids_to_keep = set()
            for (history_id,) in conn.execute(sa.text(f"select max(history_id) from {table_name} group by {columns}")):
                history_ids_to_keep.add(history_id)

            # Find all entries so we can work out which ones to
            # delete, then delete them
            all_history_ids = set()
            for (history_id,) in conn.execute(sa.text(f"select distinct history_id from {table_name}")):
                all_history_ids.add(history_id)
            history_ids_to_delete = all_history_ids - history_ids_to_keep
            if history_ids_to_delete:
                print(f"Deleting {len(history_ids_to_delete)} duplicate entries from {table_name}")
            for history_id in history_ids_to_delete:
                conn.execute(sa.text(f"delete from {table_name} where history_id={history_id}"))

        op.execute(
            f"alter table {table_name} drop constraint if exists id_version_unique_constraint"
        )
        op.create_unique_constraint(
            "id_version_unique_constraint", table_name, ["entity_id", "version"]
        )
