"""Lex domain errors."""


from typing import Dict
from karp.foundation.errors import NotFoundError


class LexDomainError(Exception):

    """Base exception for domain errors."""

    def __init__(self, *args: object, extras: Dict = None) -> None:
        super().__init__(*args)
        self.extras = extras or {}


class EntryNotFound(NotFoundError, LexDomainError):
    entity_name = "Entry"

    def __init__(self, entity_id, *args, **kwargs):
        super().__init__(entity_id, *args, **kwargs)


class ResourceNotFound(NotFoundError, LexDomainError):
    entity_name = "Resource"

    def __init__(self, entity_id, *args, msg: str):
        super().__init__(entity_id, *args, msg=msg)


class IntegrityError(LexDomainError):
    pass


class RepositoryStatusError(LexDomainError):
    pass
