from karp import errors


class SearchError(errors.KarpError):
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
