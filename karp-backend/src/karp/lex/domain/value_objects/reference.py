from dataclasses import dataclass  # noqa: D100

from karp.lex.domain.value_objects import UniqueId


@dataclass
class ResourceReference:  # noqa: D101
    resource_id: UniqueId


@dataclass
class ResourceSoftReference:  # noqa: D101
    resource_id: str


@dataclass
class EntryReference:  # noqa: D101
    resource_id: UniqueId
    entry_id: UniqueId


@dataclass
class EntrySoftReference:  # noqa: D101
    resource_id: str
    entry_id: str
