# Database migration how-to

## Initializing database or upgrading to latest version

`alembic upgrade head` (database must be created first)

## Creating new migrations

When a change has been made to the database model, run:

 `alembic revision --autogenerate -m "description of change"`

A new file is created in `alembic/versions`, this file must read and often hand-edited.
