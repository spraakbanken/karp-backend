from pathlib import Path  # noqa: D100, I001

from alembic.config import Config as AlembicConfig
import alembic
import pydantic

from karp import command_bus


class RunMigrationsUp(pydantic.BaseModel):  # noqa: D101
    to_revision: str = "head"


class RunMigrationsDown(pydantic.BaseModel):  # noqa: D101
    to_revision: str = "base"


class RunningMigrationsBase:  # noqa: D101
    def __init__(self):  # noqa: D107, ANN204
        self.alembic_cfg = AlembicConfig(Path(__file__).parent / "alembic.ini")
        self.alembic_cfg.set_main_option("script_location", str(Path(__file__).parent))


class RunningMigrationsUp(  # noqa: D101
    RunningMigrationsBase,
    command_bus.CommandHandler[RunMigrationsUp],
):
    def execute(self, command: RunMigrationsUp):  # noqa: ANN201, D102
        alembic.command.upgrade(
            self.alembic_cfg,
            command.to_revision,
        )


class RunningMigrationsDown(  # noqa: D101
    RunningMigrationsBase, command_bus.CommandHandler[RunMigrationsDown]
):
    def execute(self, command: RunMigrationsDown):  # noqa: ANN201, D102
        alembic.command.downgrade(
            self.alembic_cfg,
            command.to_revision,
        )
