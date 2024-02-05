import dataclasses  # noqa: I001

import injector


@dataclasses.dataclass
class IntegrationTestContext:
    container: injector.Injector
