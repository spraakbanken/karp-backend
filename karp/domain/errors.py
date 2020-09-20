from karp import errors


class DomainError(errors.KarpError):
    """Base exception for domain errors.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ConfigurationError(DomainError):
    """Raised when a problem with the system configuration is detected.
    """
    pass


class ConsistencyError(DomainError):
    """Raised when an internal consistency problem is detected."""

    pass


class DiscardedEntityError(DomainError):
    """Raised when an attempt is made to use a discarded Entity."""

    pass


class ConstraintsError(DomainError, ValueError):
    """Raised when a constraint is not met."""

    pass


class RepositoryError(DomainError):
    pass


class RepositoryStatusError(RepositoryError):
    pass


class SearchError(DomainError):
    def __init__(self, message, *args, **kwargs):
        if not args:
            args = [errors.ClientErrorCodes.SEARCH_GENERAL_ERROR]
        super().__init__(message, *args, **kwargs)


class IncompleteQuery(SearchError):
    def __init__(self, message):
        super().__init__(message, errors.ClientErrorCodes.SEARCH_INCOMPLETE_QUERY)


class UnsupportedQuery(SearchError):
    def __init__(self, message):
        super().__init__(message, errors.ClientErrorCodes.SEARCH_UNSUPPORTED_QUERY)


class UnsupportedField(SearchError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message, errors.ClientErrorCodes.SEARCH_UNSUPPORTED_FIELD,
        )
