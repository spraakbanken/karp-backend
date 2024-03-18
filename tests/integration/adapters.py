import dataclasses  # noqa: I001

from injector import Injector


@dataclasses.dataclass
class IntegrationTestContext:
    injector: Injector
