"""Lex domain errors."""


from typing import Dict  # noqa: I001
from karp.foundation.errors import NotFoundError


class LexDomainError(Exception):

    """Base exception for domain errors."""  # noqa: D211

    def __init__(self, *args: object, **kwargs) -> None:  # noqa: ANN003, D107
        super().__init__(*args)
        self.extras = kwargs or {}


class ConsistencyError(LexDomainError):  # noqa: D101
    pass


class ConstraintsError(LexDomainError):  # noqa: D101
    pass


class DiscardedEntityError(LexDomainError):  # noqa: D101
    pass


class EntryNotFound(NotFoundError, LexDomainError):  # noqa: D101
    entity_name = "Entry"

    def __init__(  # noqa: D107
        self, *args, entity_id=None, **kwargs  # noqa: ANN002, ANN003
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, **kwargs)
        # super().__init__(entity_id, *args, **kwargs)


class EntryRepoNotFound(NotFoundError, LexDomainError):  # noqa: D101
    entity_name = "EntryRepository"

    def __init__(  # noqa: D107
        self, entity_id, *args, **kwargs  # noqa: ANN002, ANN003
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, entity_id, *args, **kwargs)


class ResourceNotFound(NotFoundError, LexDomainError):  # noqa: D101
    entity_name = "Resource"

    def __init__(  # noqa: D107
        self, entity_id, *args, **kwargs  # noqa: ANN002, ANN003
    ) -> None:
        NotFoundError.__init__(self, entity_id, *args)
        LexDomainError.__init__(self, entity_id, *args, **kwargs)


class IntegrityError(LexDomainError):  # noqa: D101
    pass


class RepositoryError(LexDomainError):  # noqa: D101
    pass


class RepositoryStatusError(LexDomainError):  # noqa: D101
    pass


class NonExistingField(RepositoryError):
    """Raised when a field doesn't exist in a repo."""

    def __init__(self, field: str, **kwargs):  # noqa: ANN003, ANN204, D107
        # if "code" not in kwargs:
        #     kwargs["code"] = errors.ClientErrorCodes.DB_GENERAL_ERROR
        super().__init__(f"Field '{field}' doesn't exist.", **kwargs)


class InvalidEntry(LexDomainError):  # noqa: D101
    pass


class MissingIdField(InvalidEntry):  # noqa: D101
    def __init__(self, resource_id: str, entry: Dict) -> None:  # noqa: D107
        super().__init__(f"Missing ID field for resource '{resource_id}' in '{entry}'")
        self.error_obj = {
            "loc": {"resource_id": resource_id},
            "data": {"entry": entry},
            "error": {"message": str(self), "code": "missing id field"},
        }


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


class LogicError(LexDomainError):  # noqa: D101
    pass


class InvalidEntrySchema(ValueError, LogicError):  # noqa: D101
    pass


class NoSuchEntryRepository(ValueError, LexDomainError):  # noqa: D101
    pass


class DiffImposible(LexDomainError):  # noqa: D101
    pass
