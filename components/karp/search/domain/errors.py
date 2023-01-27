class DomainError(Exception):
    pass


class UnsupportedField(DomainError):
    pass


class UnsupportedQuery(DomainError):
    pass


class IncompleteQuery(DomainError):
    def __init__(
        self, failing_query: str, error_description: str, *args: object
    ) -> None:
        super().__init__(*args)
        self.failing_query = failing_query
        self.error_description = error_description
