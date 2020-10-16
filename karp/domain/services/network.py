import collections
from karp.domain.models.entry import Entry
from karp.infrastructure.unit_of_work import unit_of_work
from typing import Dict, Any, Iterator, Optional, Tuple, List
import json

from karp.domain.models.resource import Resource, ResourceRepository

# from karp.resourcemgr import get_resource
# import karp.resourcemgr.entryread as entryread
from karp.errors import EntryNotFoundError


def get_referenced_entries(
    resource_repo: ResourceRepository,
    resource: Resource,
    version: Optional[int],
    entry_id: str,
) -> Iterator[Dict[str, Any]]:
    print(f"network.get_referenced_entries: resource={resource.resource_id}")
    print(f"network.get_referenced_entries: entry_id={entry_id}")
    resource_refs, resource_backrefs = get_refs(
        resource_repo, resource.resource_id, version=version
    )

    with unit_of_work(using=resource.entry_repository) as uw:
        src_entry = uw.by_entry_id(entry_id, version=version)
        if not src_entry:
            raise EntryNotFoundError(
                resource.resource_id, entry_id, resource_version=resource.version
            )

    with unit_of_work(using=resource_repo) as resources_uw:
        for (
            ref_resource_id,
            ref_resource_version,
            field_name,
            field,
        ) in resource_backrefs:
            other_resource = resources_uw.by_resource_id(
                ref_resource_id, version=version
            )
            with unit_of_work(using=other_resource.entry_repository) as entries_uw:
                for entry in entries_uw.by_referenceable({field_name: entry_id}):
                    yield _create_ref(ref_resource_id, ref_resource_version, entry)

        # src_body = json.loads(src_entry.body)
        for (ref_resource_id, ref_resource_version, field_name, field) in resource_refs:
            ids = src_entry.body.get(field_name)
            if not field.get("collection", False):
                ids = [ids]
            ref_resource = resources_uw.by_resource_id(ref_resource_id)
            if ref_resource:
                with unit_of_work(using=ref_resource.entry_repository) as entries_uw:
                    for ref_entry_id in ids:
                        entry = entries_uw.by_entry_id(
                            ref_entry_id, version=ref_resource_version
                        )
                        if entry:
                            yield _create_ref(
                                ref_resource_id, ref_resource_version, entry
                            )


def get_refs(
    resource_repo: ResourceRepository, resource_id, version=None
) -> Tuple[List[Tuple[str, int, str, Dict]], List[Tuple[str, int, str, Dict]]]:
    """
    Goes through all other resource configs finding resources and fields that refer to this resource
    """
    resource_backrefs = collections.defaultdict(lambda: collections.defaultdict(dict))
    resource_refs = collections.defaultdict(lambda: collections.defaultdict(dict))

    with unit_of_work(using=resource_repo) as uw:
        src_resource = uw.by_resource_id(resource_id, version=version)

        all_other_resources = [
            resource
            for resource in uw.get_published_resources()
            if resource.resource_id != resource_id
            # or resource_def.version != version
        ]

    for field_name, field in src_resource.config["fields"].items():
        if "ref" in field:
            if "resource_id" not in field["ref"]:
                resource_backrefs[resource_id][version][field_name] = field
                resource_refs[resource_id][version][field_name] = field
            else:
                resource_refs[field["ref"]["resource_id"]][
                    field["ref"]["resource_version"]
                ][field_name] = field
        elif "function" in field and "multi_ref" in field["function"]:
            virtual_field = field["function"]["multi_ref"]
            ref_field = virtual_field["field"]
            if "resource_id" in virtual_field:
                resource_backrefs[virtual_field["resource_id"]][
                    virtual_field["resource_version"]
                ][ref_field] = None
            else:
                resource_backrefs[resource_id][version][ref_field] = None

    for other_resource in all_other_resources:
        # other_resource = get_resource(
        #     resource_def.resource_id, version=resource_def.version
        # )
        for field_name, field in other_resource.config["fields"].items():
            ref = field.get("ref")
            if (
                ref
                and ref.get("resource_id") == resource_id
                and ref.get("resource_version") == version
            ):
                resource_backrefs[other_resource.resource_id][other_resource.version][
                    field_name
                ] = field

    def flatten_dict(ref_dict):
        ref_list = []
        for ref_resource_id, versions in ref_dict.items():
            for ref_version, field_names in versions.items():
                for field_name, field in field_names.items():
                    ref_list.append((ref_resource_id, ref_version, field_name, field))
        return ref_list

    return flatten_dict(resource_refs), flatten_dict(resource_backrefs)


def _create_ref(
    resource_id: str, resource_version: int, entry: Entry
) -> Dict[str, Any]:
    return {
        "resource_id": resource_id,
        "resource_version": resource_version,
        "entry": entry,
    }
