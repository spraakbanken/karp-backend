"""Lex domain errors."""


from typing import Dict  # noqa: I001
from karp.foundation.errors import NotFoundError


class LexDomainError(Exception):

    """Base exception for domain errors."""

    def __init__(self, *args: object, **kwargs) -> None:
        super().__init__(*args)
        self.extras = kwargs or {}


class DiscardedEntityError(LexDomainError):
    pass


class EntryNotFound(NotFoundError, LexDomainError):
    entity_name = "Entry"

    def __init__(
        self,
        *args,
        entity_id=None,
        **kwargs,
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, **kwargs)
        # super().__init__(entity_id, *args, **kwargs)


class ResourceNotFound(NotFoundError, LexDomainError):
    entity_name = "Resource"

    def __init__(
        self,
        entity_id,
        *args,
        **kwargs,
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, entity_id, *args, **kwargs)


class IntegrityError(LexDomainError):
    pass


class RepositoryError(LexDomainError):
    pass


class InvalidEntry(LexDomainError):
    pass


class UpdateConflict(LexDomainError):
    def __init__(self, diff):
        super().__init__(
            "Version conflict. Please update entry.",
        )
        self.error_obj = {"diff": diff, "error": str(self)}


class LexValueError(ValueError, LexDomainError):
    pass


class InvalidResourceId(LexValueError):
    pass


class InvalidEntrySchema(ValueError, LexDomainError):
    pass


class NoSuchEntryRepository(ValueError, LexDomainError):
    pass


class DiffImposible(LexDomainError):
    pass
