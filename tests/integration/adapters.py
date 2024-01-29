import dataclasses  # noqa: I001

import injector

from karp.foundation.events import EventBus


@dataclasses.dataclass
class IntegrationTestContext:
    container: injector.Injector
    event_bus: EventBus
