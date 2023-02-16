class DomainError(Exception):  # noqa: D100, D101
    pass


class UnsupportedField(DomainError):  # noqa: D101
    pass


class UnsupportedQuery(DomainError):  # noqa: D101
    pass


class IncompleteQuery(DomainError):  # noqa: D101
    def __init__(  # noqa: D107
        self, failing_query: str, error_description: str, *args: object
    ) -> None:
        super().__init__(*args)
        self.failing_query = failing_query
        self.error_description = error_description
