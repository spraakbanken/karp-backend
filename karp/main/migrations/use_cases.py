from pathlib import Path

from alembic.config import Config as AlembicConfig
import alembic
import pydantic

from karp.foundation import commands


class RunMigrationsUp(pydantic.BaseModel):
    pass


class RunningMigrationsUp(
    commands.CommandHandler[RunMigrationsUp]
):
    def execute(self, _command: RunMigrationsUp):
        alembic_cfg = AlembicConfig(
            Path(__file__).parent / 'alembic.ini'
        )
        alembic.command.upgrade(alembic_cfg, 'head')
