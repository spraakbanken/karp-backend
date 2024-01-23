import pydantic

from karp.lex_core.value_objects import UniqueIdStr


class EntryRepoDto(pydantic.BaseModel):  # noqa: D101
    name: str
    entity_id: UniqueIdStr
