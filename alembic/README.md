# Database migration how-to

## Initializing database

Run `alembic upgrade head` on a clean database.

## Creating new migrations

When a change has been made to the database model, run:

 `alembic revision --autogenerate -m "description of change"`

A new file is created in `alembic/versions`, this file must read and often hand-edited.

If changes have been made to the tables `dummy_entry` or `dummy_history`, add the following import to the code:

```
from karp.migration_helper import entry_tables, history_tables
 ```

Add the following code if either `dummy_entry` or `dummy_history` is in `upgrade`, for example if the change made was:

```
op.add_column('dummy_entry', sa.Column('new_col', sa.Boolean(), nullable=True))
```

add:

```
 for entry_table in entry_tables:
     op.add_column(entry_table, sa.Column('new_col', sa.Boolean(), nullable=True))
 ```

Ignore downgrade.

## Upgrading to latest version

Run `alembic upgrade head`
