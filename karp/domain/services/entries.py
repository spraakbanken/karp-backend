from typing import List

from karp.domain.models.entry import Entry
from karp.domain.models.resource import Resource
from karp.infrastructure.unit_of_work import unit_of_work


def add_entry(resource: Resource, entry: Entry) -> str:
    return add_entries(resource, [entry])[0]


def add_entries(resource: Resource, entries: List[Entry]) -> List[str]:
    if resource is None:
        raise ValueError("Must provide resource.")

    entry_ids = []
    with unit_of_work(using=resource.entry_repository) as uw:
        for entry in entries:
            uw.put(entry)
            entry_ids.append(entry.entry_id)

    return entry_ids
