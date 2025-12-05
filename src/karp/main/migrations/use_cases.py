from pathlib import Path  # noqa: I001

from alembic.config import Config as AlembicConfig
import alembic


alembic_cfg = AlembicConfig(Path(__file__).parent / "alembic.ini")
alembic_cfg.set_main_option("script_location", str(Path(__file__).parent))


def run_migrations_up():
    alembic.command.upgrade(
        alembic_cfg,
        "head",
    )


def run_migrations_down():
    alembic.command.downgrade(
        alembic_cfg,
        "base",
    )
