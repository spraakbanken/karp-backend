"""Lex domain errors."""


from typing import Dict  # noqa: I001
from karp.foundation.errors import NotFoundError


class LexDomainError(Exception):

    """Base exception for domain errors."""  # noqa: D211

    def __init__(self, *args: object, **kwargs) -> None:  # noqa: ANN003, D107
        super().__init__(*args)
        self.extras = kwargs or {}


class DiscardedEntityError(LexDomainError):  # noqa: D101
    pass


class EntryNotFound(NotFoundError, LexDomainError):  # noqa: D101
    entity_name = "Entry"

    def __init__(  # noqa: D107
        self,
        *args,
        entity_id=None,
        **kwargs,  # noqa: ANN002, ANN003
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, **kwargs)
        # super().__init__(entity_id, *args, **kwargs)


class ResourceNotFound(NotFoundError, LexDomainError):  # noqa: D101
    entity_name = "Resource"

    def __init__(  # noqa: D107
        self,
        entity_id,
        *args,
        **kwargs,  # noqa: ANN002, ANN003
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, entity_id, *args, **kwargs)


class IntegrityError(LexDomainError):  # noqa: D101
    pass


class RepositoryError(LexDomainError):  # noqa: D101
    pass


class InvalidEntry(LexDomainError):  # noqa: D101
    pass


class UpdateConflict(LexDomainError):  # noqa: D101
    def __init__(self, diff):  # noqa: D107, ANN204
        super().__init__(
            "Version conflict. Please update entry.",
        )
        self.error_obj = {"diff": diff, "error": str(self)}


class LexValueError(ValueError, LexDomainError):  # noqa: D101
    pass


class InvalidResourceId(LexValueError):  # noqa: D101
    pass


class InvalidEntrySchema(ValueError, LexDomainError):  # noqa: D101
    pass


class NoSuchEntryRepository(ValueError, LexDomainError):  # noqa: D101
    pass


class DiffImposible(LexDomainError):  # noqa: D101
    pass
