from pathlib import Path

from alembic.config import Config as AlembicConfig
import alembic
import pydantic

from karp import command_bus


class RunMigrationsUp(pydantic.BaseModel):
    to_revision: str = "head"


class RunMigrationsDown(pydantic.BaseModel):
    to_revision: str = "base"


class RunningMigrationsBase:
    def __init__(self):
        self.alembic_cfg = AlembicConfig(Path(__file__).parent / "alembic.ini")
        self.alembic_cfg.set_main_option("script_location", str(Path(__file__).parent))


class RunningMigrationsUp(
    RunningMigrationsBase,
    command_bus.CommandHandler[RunMigrationsUp],
):
    def execute(self, command: RunMigrationsUp):
        alembic.command.upgrade(
            self.alembic_cfg,
            command.to_revision,
        )


class RunningMigrationsDown(
    RunningMigrationsBase, command_bus.CommandHandler[RunMigrationsDown]
):
    def execute(self, command: RunMigrationsDown):
        alembic.command.downgrade(
            self.alembic_cfg,
            command.to_revision,
        )
