"""Lex domain errors."""


from typing import Dict
from karp.foundation.errors import NotFoundError


class LexDomainError(Exception):

    """Base exception for domain errors."""

    def __init__(self, *args: object, **kwargs) -> None:
        super().__init__(*args)
        self.extras = kwargs or {}


class ConsistencyError(LexDomainError):
    pass


class ConstraintsError(LexDomainError):
    pass


class DiscardedEntityError(LexDomainError):
    pass


class EntryNotFound(NotFoundError, LexDomainError):
    entity_name = "Entry"

    def __init__(self, *args, entity_id=None, **kwargs):
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, **kwargs)
        # super().__init__(entity_id, *args, **kwargs)


class EntryRepoNotFound(NotFoundError, LexDomainError):
    entity_name = "EntryRepository"

    def __init__(self, entity_id, *args, **kwargs):
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, entity_id, *args, **kwargs)


class ResourceNotFound(NotFoundError, LexDomainError):
    entity_name = "Resource"

    def __init__(self, entity_id, *args, **kwargs):
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, entity_id, *args, **kwargs)


class IntegrityError(LexDomainError):
    pass


class RepositoryError(LexDomainError):
    pass


class RepositoryStatusError(LexDomainError):
    pass


class InvalidEntry(LexDomainError):
    pass


class MissingIdField(InvalidEntry):
    def __init__(self, resource_id: str, entry: Dict) -> None:
        super().__init__(
            f"Missing ID field for resource '{resource_id}' in '{entry}'")
        self.error_obj = {
            'loc': {'resource_id': resource_id}, 'data': {'entry': entry}, 'error': {'message': str(self), 'code': 'missing id field'}}


class UpdateConflict(LexDomainError):
    def __init__(self, diff):
        super().__init__(
            "Version conflict. Please update entry.",
        )
        self.error_obj = {"diff": diff,
                          "error": str(self)}
