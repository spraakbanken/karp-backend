from karp import errors


class SearchError(errors.KarpError):
    def __init__(self, message):
        super().__init__(message)


class IncompleteQuery(SearchError):
    def __init__(self, message):
        super().__init__(message)
