"""timestamps

Revision ID: 31f8e4fcc764
Revises: 5bb29472d33f
Create Date: 2019-04-23 15:34:28.419377

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '31f8e4fcc764'
down_revision = '5bb29472d33f'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('dummy_history', 'timestamp',
                    server_default=None,
                    existing_type=sa.DateTime(),
                    type_=sa.Integer(),
                    existing_nullable=False)

    # every history table needs the following done, but don't know how to express that in alembic
    """
    ALTER TABLE saldo_1_history ADD timestamp2 INTEGER not null;
    SELECT t1.entry_id, t2.entry_id, unix_timestamp(t2.timestamp) from saldo_1_history as t1 JOIN saldo_1_history as t2 ON t1.id = t2.id;
    UPDATE saldo_1_history as t1 JOIN saldo_1_history as t2 ON t1.id = t2.id SET t1.timestamp2 = unix_timestamp(t2.timestamp);
    ALTER TABLE saldo_1_history DROP COLUMN timestamp;
    ALTER TABLE saldo_1_history CHANGE COLUMN `timestamp2` timestamp integer not null;
    """
    # 1. add tmp column
    # 2. check that it works
    # 3. copy timestamps to tmp column
    # 4. remove old column
    # 5. rename tmp column to timestamp


def downgrade():
    pass
