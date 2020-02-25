from karp import errors


class SearchError(errors.KarpError):
    def __init__(self, message):
        super().__init__(message, errors.ClientErrorCodes.SEARCH_GENERAL_ERROR)


class IncompleteQuery(errors.KarpError):
    def __init__(self, message):
        super().__init__(message, errors.ClientErrorCodes.SEARCH_INCOMPLETE_QUERY)


class UnsupportedQuery(errors.KarpError):
    def __init__(self, message):
        super().__init__(message, errors.ClientErrorCodes.SEARCH_UNSUPPORTED_QUERY)
