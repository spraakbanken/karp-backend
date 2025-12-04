import logging
from copy import deepcopy

from karp.lex.domain.dtos import EntryDto
from karp.search.domain.index_entry import IndexEntry
from karp.search.infrastructure.es import mapping_repo

logger = logging.getLogger(__name__)

"""
TODO this module doesn't do much anymore, refactor
"""


def transform(src_entry: EntryDto) -> IndexEntry:
    entry = deepcopy(src_entry.entry)
    for mapped_name, field in mapping_repo.internal_fields.items():
        entry[field.name] = getattr(src_entry, mapped_name)
    return IndexEntry(id=str(src_entry.id), entry=entry)
