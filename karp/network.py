from typing import Dict, Any, Iterator, Optional
import json

from karp.resourcemgr import get_resource, get_refs
import karp.resourcemgr.entryread as entryread
from karp.errors import EntryNotFoundError


def get_referenced_entries(
    resource_id: str, version: Optional[int], entry_id: str
) -> Iterator[Dict[str, Any]]:
    resource_refs, resource_backrefs = get_refs(resource_id, version=version)

    src_entry = entryread.get_entry(resource_id, entry_id, version=version)
    if not src_entry:
        raise EntryNotFoundError(resource_id, entry_id, resource_version=version)

    for (ref_resource_id, ref_resource_version, field_name, field) in resource_backrefs:
        resource = get_resource(ref_resource_id, version=version)
        for entry in entryread.get_entries_by_column(resource, {field_name: entry_id}):
            yield _create_ref(
                ref_resource_id,
                ref_resource_version,
                entry["id"],
                entry["entry_id"],
                entry["entry"],
            )

    src_body = json.loads(src_entry.body)
    for (ref_resource_id, ref_resource_version, field_name, field) in resource_refs:
        ids = src_body.get(field_name)
        if not field.get("collection", False):
            ids = [ids]
        for ref_entry_id in ids:
            entry = entryread.get_entry(
                ref_resource_id, ref_entry_id, version=ref_resource_version
            )
            if entry:
                yield _create_ref(
                    ref_resource_id,
                    ref_resource_version,
                    entry.id,
                    entry.entry_id,
                    json.loads(entry.body),
                )


def _create_ref(
    resource_id: str, resource_version: int, _id: int, entry_id: str, entry_body: Dict
) -> Dict[str, Any]:
    return {
        "resource_id": resource_id,
        "resource_version": resource_version,
        "id": _id,
        "entry_id": entry_id,
        "entry": entry_body,
    }
