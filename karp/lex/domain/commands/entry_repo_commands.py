import pydantic

from karp.lex.domain.value_objects import UniqueId

from .base import Command


class CreateEntryRepository(Command):
    entity_id: UniqueId
