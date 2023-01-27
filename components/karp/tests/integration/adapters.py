import dataclasses

import injector

from karp.foundation.commands import CommandBus
from karp.foundation.events import EventBus


@dataclasses.dataclass
class IntegrationTestContext:
    container: injector.Injector
    command_bus: CommandBus
    event_bus: EventBus
