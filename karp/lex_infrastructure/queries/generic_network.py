import collections
import logging
import typing

# from karp.infrastructure.unit_of_work import unit_of_work
from typing import Any, Dict, Iterator, List, Optional, Tuple
from karp.foundation.value_objects.unique_id import UniqueId
from karp.lex.application.queries.entries import EntryDto

from karp.lex.domain import entities
from karp.lex.domain.entities.entry import Entry
from karp.lex.application.queries import (
    GetReferencedEntries,
    ReferenceDto,
    ReadOnlyResourceRepository,
)
from karp.lex.application.repositories import EntryUowRepositoryUnitOfWork

# from karp.resourcemgr import get_resource
# import karp.resourcemgr.entryread as entryread
from karp.lex.domain.errors import EntryNotFound

# from karp.services import context

logger = logging.getLogger(__name__)


class GenericGetReferencedEntries(GetReferencedEntries):
    def __init__(
        self,
        resource_repo: ReadOnlyResourceRepository,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> None:
        super().__init__()
        self.resource_repo = resource_repo
        self.entry_repo_uow = entry_repo_uow

    def query(
        self,
        resource_id: str,
        # version: typing.Optional[int],
        entry_id: UniqueId,
    ) -> typing.Iterable[ReferenceDto]:
        logger.debug(f"network.get_referenced_entries: resource_id={resource_id}")
        logger.debug(f"network.get_referenced_entries: entry_id={entry_id}")
        resource_refs, resource_backrefs = self.get_refs(
            resource_id,  # version=version
        )

        resource = self.resource_repo.get_by_resource_id(resource_id)
        if not resource:
            raise RuntimeError(f"resource '{resource_id}' not found")
        with self.entry_repo_uow:
            entry_uow = self.entry_repo_uow.repo.get_by_id(resource.entry_repository_id)
        with entry_uow as uw:
            src_entry = uw.repo.by_id(
                entry_id,  # version=version
            )
            # if not src_entry:
            #     raise EntryNotFoundError(
            #         resource.resource_id, entry_id, resource_version=resource.version
            #     )

        for (
            ref_resource_id,
            ref_resource_version,
            field_name,
            field,
        ) in resource_backrefs:
            other_resource = self.resource_repo.get_by_resource_id(
                ref_resource_id  # , version=version
            )
            if not other_resource:
                logger.info("resource %s not found, skipping ...", ref_resource_id)
                continue
            with self.entry_repo_uow:
                other_entry_uow = self.entry_repo_uow.repo.get_by_id(
                    other_resource.entry_repository_id
                )
            with other_entry_uow as entries_uw:
                for entry in entries_uw.repo.by_referenceable({field_name: entry_id}):
                    yield _create_ref(ref_resource_id, ref_resource_version, entry)

        # src_body = json.loads(src_entry.body)
        for (ref_resource_id, ref_resource_version, field_name, field) in resource_refs:
            ids = src_entry.body.get(field_name)
            if ids is None:
                continue
            if not field.get("collection", False):
                ids = [ids]
            if ref_resource := self.resource_repo.get_by_resource_id(ref_resource_id):
                with self.entry_repo_uow.repo.get_by_id(
                    ref_resource.entry_repository_id
                ) as entries_uw:
                    for ref_entry_id in ids:
                        if entry := entries_uw.repo.get_by_id_optional(
                            ref_entry_id, version=ref_resource_version
                        ):
                            yield _create_ref(
                                ref_resource_id, ref_resource_version, entry
                            )

    def get_refs(
        self, resource_id, version=None
    ) -> Tuple[List[Tuple[str, int, str, Dict]], List[Tuple[str, int, str, Dict]]]:
        """
        Goes through all other resource configs finding resources and fields that refer to this resource
        """
        resource_backrefs = collections.defaultdict(
            lambda: collections.defaultdict(dict)
        )
        resource_refs = collections.defaultdict(lambda: collections.defaultdict(dict))

        src_resource = self.resource_repo.get_by_resource_id(
            resource_id, version=version
        )

        if not src_resource:
            raise RuntimeError(f"Can't find resource '{resource_id}'")
        all_other_resources = [
            resource
            for resource in self.resource_repo.get_published_resources()
            if resource.resource_id != resource_id
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
                    resource_backrefs[other_resource.resource_id][
                        other_resource.version
                    ][field_name] = field

        def flatten_dict(ref_dict):
            ref_list = []
            for ref_resource_id, versions in ref_dict.items():
                for ref_version, field_names in versions.items():
                    for field_name, field in field_names.items():
                        ref_list.append(
                            (ref_resource_id, ref_version, field_name, field)
                        )
            return ref_list

        return flatten_dict(resource_refs), flatten_dict(resource_backrefs)


def _create_ref(resource_id: str, resource_version: int, entry: Entry) -> ReferenceDto:
    return ReferenceDto(
        resource_id=resource_id,
        resource_version=resource_version,
        entry=EntryDto(**entry.dict()),
    )
