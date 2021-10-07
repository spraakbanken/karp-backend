"""Lex domain errors."""


from karp.domain.errors import NonExistingField
from typing import Dict


class LexDomainError(Exception):

    """Base exception for domain errors."""

    def __init__(self, *args: object, extras: Dict = None) -> None:
        super().__init__(*args)
        self.extras = extras or {}


class EntryNotFound(NotFoundError):
    entity_name = "Entry"

    def __init__(self, entity_id, *args, **kwargs):
        super().__init__(entity_id, *args, **kwargs)
