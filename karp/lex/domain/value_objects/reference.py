from dataclasses import dataclass

from karp.lex.domain.value_objects import UniqueId


@dataclass
class ResourceReference:
    resource_id: UniqueId


@dataclass
class ResourceSoftReference:
    resource_id: str


@dataclass
class EntryReference:
    resource_id: UniqueId
    entry_id: UniqueId


@dataclass
class EntrySoftReference:
    resource_id: str
    entry_id: str
