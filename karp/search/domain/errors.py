class DomainError(Exception):
    pass


class UnsupportedField(DomainError):
    pass


class UnsupportedQuery(DomainError):
    pass


class IncompleteQuery(DomainError):
    pass
