class NotFoundError(Exception):  # noqa: D100
    """Generic not found error."""

    entity_name: str = "Generic entity"

    def __init__(  # noqa: D107
        self,
        entity_id,
        *args,
        msg: str | None = None,  # noqa: ANN002
    ) -> None:
        msg = msg or f"{self.entity_name} not found. Id: {entity_id}"
        super().__init__(msg, *args)


class DiscardedEntityError(Exception):
    """Raised when an attempt is made to use a discarded Entity."""


class ConsistencyError(Exception):
    """Raised when an internal consistency problem is detected."""