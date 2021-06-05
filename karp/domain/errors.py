from karp import errors


class DomainError(errors.KarpError):
    """Base exception for domain errors."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EntryNotFound(DomainError):
    def __init__(
        self,
        entry_id: str,
        resource_id: str,
        resource_version: int = None,
        **kwargs,
    ):
        super().__init__(
            f"Entry '{entry_id}' not found in resource '{resource_id}' (version={resource_version or 'latest'})",
            code=errors.ClientErrorCodes.ENTRY_NOT_FOUND,
            **kwargs,
        )


class ConfigurationError(DomainError):
    """Raised when a problem with the system configuration is detected."""

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


class ResourceNotFound(DomainError):
    """Raised when a resource is missing."""

    def __init__(self, resource_id, **kwargs):
        super().__init__(f"Resource '{resource_id}' not found.", **kwargs)


class ResourceNotPublished(DomainError):
    """Raised when a resource is not published."""

    def __init__(self, resource_id, **kwargs):
        super().__init__(f"Resource '{resource_id}' is not published.", **kwargs)


class RepositoryError(DomainError):
    def __init__(self, message: str, **kwargs):
        if "code" not in kwargs:
            kwargs["code"] = errors.ClientErrorCodes.DB_GENERAL_ERROR
        super().__init__(message, **kwargs)


class RepositoryStatusError(RepositoryError):
    def __init__(self, message: str, **kwargs):
        if "code" not in kwargs:
            kwargs["code"] = errors.ClientErrorCodes.DB_GENERAL_ERROR
        super().__init__(message, **kwargs)


class IntegrityError(RepositoryError):
    """Raised when a ..."""

    def __init__(self, message: str, **kwargs) -> None:
        if "code" not in kwargs:
            kwargs["code"] = errors.ClientErrorCodes.DB_INTEGRITY_ERROR
        super().__init__(message, **kwargs)


class NonExistingField(RepositoryError):
    """Raised when a field doesn't exist in a repo."""

    def __init__(self, field: str, **kwargs):
        if "code" not in kwargs:
            kwargs["code"] = errors.ClientErrorCodes.DB_GENERAL_ERROR
        super().__init__(f"Field '{field}' doesn't exist.", **kwargs)


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
            message,
            errors.ClientErrorCodes.SEARCH_UNSUPPORTED_FIELD,
        )


class AuthError(DomainError):
    """Raised when there is an error with authentication or authorizing."""

    def __init__(self, message: str, **kwargs) -> None:
        if "code" not in kwargs:
            kwargs["code"] = errors.ClientErrorCodes.AUTH_GENERAL_ERROR
        super().__init__(message, **kwargs)


class UpdateConflict(DomainError):
    def __init__(self, diff):
        super().__init__(
            "Version conflict. Please update entry.",
            code=errors.ClientErrorCodes.VERSION_CONFLICT,
        )
        self.error_obj = {"diff": diff, "errorCode": self.code, "error": self.message}
