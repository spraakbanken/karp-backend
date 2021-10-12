from typing import Dict

import pydantic

from karp.lex.domain.value_objects import UniqueId

from .base import Command


class CreateEntryRepository(Command):
    entity_id: UniqueId
    repository_type: str
    name: str
    config: Dict
