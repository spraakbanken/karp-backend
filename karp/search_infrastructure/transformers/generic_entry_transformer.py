import collections
import logging
import typing

import logging

from karp.lex.application.queries.resources import ResourceDto

from karp.lex.domain import entities, errors as lex_errors
from karp.lex.application.queries import (
    GetReferencedEntries,
    ReadOnlyResourceRepository,
    EntryViews,
    EntryDto,
)
from karp.lex.application.repositories import (
    ResourceUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)
from karp.search.application.transformers import EntryTransformer
from karp.search.application.repositories import IndexUnitOfWork, IndexEntry


logger = logging.getLogger(__name__)


class GenericEntryTransformer(EntryTransformer):
    def __init__(
        self,
        index_uow: IndexUnitOfWork,
        resource_repo: ReadOnlyResourceRepository,
        entry_views: EntryViews,
        get_referenced_entries: GetReferencedEntries,
    ) -> None:
        super().__init__()
        self.index_uow = index_uow
        self.resource_repo = resource_repo
        self.entry_views = entry_views
        self.get_referenced_entries = get_referenced_entries

    def transform(self, resource_id: str, src_entry: EntryDto) -> IndexEntry:
        """
        TODO This is very slow (for resources with references) because of db-lookups everywhere in the code
        TODO We can pre-fetch the needed entries (same code that only looks for refs?) or
        TODO somehow get the needed entries in bulk after transforming some entries and insert them into
        TODO the transformed entries afterward. Very tricky.
        """
        logger.debug(
            "transforming entry",
            extra={"entity_id": src_entry.entity_id, "resource_id": resource_id},
        )
        index_entry = self.index_uow.repo.create_empty_object()
        index_entry.id = str(src_entry.entity_id)
        self.index_uow.repo.assign_field(
            index_entry, "_entry_version", src_entry.version
        )
        self.index_uow.repo.assign_field(
            index_entry, "_last_modified", src_entry.last_modified
        )
        self.index_uow.repo.assign_field(
            index_entry, "_last_modified_by", src_entry.last_modified_by
        )
        resource = self.resource_repo.get_by_resource_id(resource_id)
        if not resource:
            raise lex_errors.ResourceNotFound(None, resource_id=resource_id)
        self._transform_to_index_entry(
            resource,
            # resource_repo,
            # indexer,
            src_entry.entry,
            index_entry,
            resource.config["fields"].items(),
        )
        logger.debug(
            "transformed entry", extra={"entry": src_entry, "index_entry": index_entry}
        )
        return index_entry

    def _transform_to_index_entry(
        self,
        resource: ResourceDto,
        # resource_repo: ResourceRepository,
        # indexer: SearchService,
        _src_entry: typing.Dict,
        _index_entry: IndexEntry,
        fields,
    ):
        logger.debug("transforming [part of] entry", extra={"src_entry": _src_entry})
        for field_name, field_conf in fields:
            field_content = None
            if field_conf.get("virtual"):
                logger.debug("found virtual field")
                if res := self._evaluate_function(
                    field_conf["function"], _src_entry, resource
                ):
                    self.index_uow.repo.assign_field(
                        _index_entry, f"v_{field_name}", res
                    )
            elif field_conf.get("collection"):
                field_content = self.index_uow.repo.create_empty_list()
                if field_name in _src_entry:
                    for subfield in _src_entry[field_name]:
                        if field_conf["type"] == "object":
                            subfield_content = self.index_uow.repo.create_empty_object()
                            self._transform_to_index_entry(
                                resource,
                                subfield,
                                subfield_content,
                                field_conf["fields"].items(),
                            )
                            self.index_uow.repo.add_to_list_field(
                                field_content, subfield_content.entry
                            )
                        else:
                            self.index_uow.repo.add_to_list_field(
                                field_content, subfield
                            )
            elif field_conf["type"] == "object":
                field_content = self.index_uow.repo.create_empty_object()
                if field_name in _src_entry:
                    self._transform_to_index_entry(
                        resource,
                        _src_entry[field_name],
                        field_content,
                        field_conf["fields"].items(),
                    )
            elif field_conf["type"] in (
                "integer",
                "string",
                "number",
                "boolean",
                "long_string",
            ):
                if field_name in _src_entry:
                    field_content = _src_entry[field_name]

            if field_content:
                self.index_uow.repo.assign_field(
                    _index_entry, field_name, field_content
                )

            # Handle ref
            if field_conf.get("ref") and field_name in _src_entry:
                if res := self._resolve_ref(
                    resource, _src_entry, field_conf["ref"], field_name
                ):
                    self.index_uow.repo.assign_field(
                        _index_entry, f"v_{field_name}", res
                    )

    def _resolve_ref(
        self,
        resource: ResourceDto,
        src_entry: dict,
        ref_conf: dict,
        field_name: str,
    ) -> typing.Optional[typing.Any]:
        res = None
        if "resource_id" in ref_conf:
            ref_resource = self.resource_repo.get_by_resource_id(
                ref_conf["resource_id"], version=ref_conf.get("resource_version")
            )
        else:
            ref_resource = resource

        if not ref_resource:
            return res
        try:
            if ref_conf["field"].get("collection"):
                res = self.index_uow.repo.create_empty_list()
                for ref_id in src_entry[field_name]:
                    if ref_entry_body := self.entry_views.get_by_id_optional(
                        ref_resource.resource_id, str(ref_id)
                    ):
                        # ref_entry = {
                        #     field_name: ref_entry_body.entry
                        # }
                        ref_entry = ref_entry_body.entry
                        if ref_conf["field"]["type"] == "object":
                            ref_index_entry = self.index_uow.repo.create_empty_object()
                            for ref_field_name, _ref_field_conf in ref_conf["field"][
                                "fields"
                            ].items():
                                self.index_uow.repo.assign_field(
                                    ref_index_entry,
                                    ref_field_name,
                                    ref_entry[ref_field_name],
                                )
                                self.index_uow.repo.add_to_list_field(
                                    res, ref_index_entry
                                )
                    # ref_objs = []
                    # if ref_resource:
                    #     for ref_id in _src_entry[field_name]:
                    #         ref_entry_body = self.entry_views.get_by_entry_id_optional(
                    #             ref_field['resource_id'], str(ref_id))
                    #         if ref_entry_body:
                    #             ref_entry = {
                    #                 field_name: ref_entry_body.entry}
                    #             ref_index_entry = (
                    #                 self.index_uow.repo.create_empty_object()
                    #             )
                    #             list_of_sub_fields = (
                    #                 (field_name, ref_field["field"]),)
                    #             self._transform_to_index_entry(
                    #                 resource,
                    #                 # resource_repo,
                    #                 # indexer,
                    #                 ref_entry,
                    #                 ref_index_entry,
                    #                 list_of_sub_fields,
                    #             )
                    #             ref_objs.append(
                    #                 ref_index_entry.entry[field_name])
                    # self.index_uow.repo.assign_field(
                    #     _index_entry, "v_" + field_name, ref_objs
                    # )
            elif ref := self.entry_views.get_by_id_optional(
                ref_resource.resource_id, str(src_entry[field_name])
            ):
                ref_entry = {field_name: ref.entry}
                ref_index_entry = self.index_uow.repo.create_empty_object()
                list_of_sub_fields = ((field_name, ref_conf["field"]),)
                self._transform_to_index_entry(
                    ref_resource,
                    ref_entry,
                    ref_index_entry,
                    list_of_sub_fields,
                )
                res = ref_index_entry.entry[field_name]
            return res
        except ValueError as exc:
            logger.warning(
                "Got ValueError (%s)",
                str(exc),
                extra={"exc": exc, "resource": resource},
            )

        # if field_conf["type"] == "object":
        #     logger.debug("found field with type 'object'")
        #     field_content = self.index_uow.repo.create_empty_object()
        #     if field_name in _src_entry:
        #         self._transform_to_index_entry(
        #             resource,
        #             # resource_repo,
        #             # indexer,
        #             _src_entry[field_name],
        #             field_content,
        #             field_conf["fields"].items(),
        #         )
        # else:
        #     field_content = _src_entry.get(field_name)

    def _evaluate_function(
        self,
        # resource_repo: ResourceRepository,
        # indexer: SearchService,
        function_conf: typing.Dict,
        src_entry: typing.Dict,
        src_resource: ResourceDto,
    ):
        logger.debug(
            "indexing._evaluate_function",
            extra={"src_resource": src_resource.resource_id},
        )
        logger.debug("indexing._evaluate_function", extra={"src_entry": src_entry})
        if "multi_ref" in function_conf:
            function_conf = function_conf["multi_ref"]
            target_field = function_conf["field"]
            if "resource_id" in function_conf:
                logger.debug(
                    "indexing._evaluate_function: trying to find '%s'",
                    function_conf["resource_id"],
                )
                target_resource = self.resource_repo.get_by_resource_id(
                    function_conf["resource_id"],
                    version=function_conf["resource_version"],
                )
                if target_resource is None:
                    logger.warning(
                        "Didn't find the resource with resource_id='%s'",
                        function_conf["resource_id"],
                    )
                    return self.index_uow.repo.create_empty_list()
            else:
                target_resource = src_resource
            logger.debug(
                "indexing._evaluate_function target_resource='%s'",
                target_resource.resource_id,
            )
            if "test" in function_conf:
                operator, args = list(function_conf["test"].items())[0]
                if operator in ["equals", "contains"]:
                    filters = {"discarded": False}
                    for arg in args:
                        if "self" in arg:
                            filters[target_field] = src_entry[arg["self"]]
                        else:
                            raise NotImplementedError()
                    # target_entries = entryread.get_entries_by_column(
                    #     target_resource, filters
                    # )
                    target_entries = self.entry_views.get_by_referenceable(
                        target_resource.resource_id, filters
                    )
                else:
                    raise NotImplementedError()
            else:
                raise NotImplementedError()

            res = self.index_uow.repo.create_empty_list()
            for entry in target_entries:
                index_entry = self.index_uow.repo.create_empty_object()
                list_of_sub_fields = (("tmp", function_conf["result"]),)
                self._transform_to_index_entry(
                    target_resource,
                    # resource_repo,
                    # indexer,
                    {"tmp": entry.entry},
                    index_entry,
                    list_of_sub_fields,
                )
                self.index_uow.repo.add_to_list_field(res, index_entry.entry["tmp"])
        elif "plugin" in function_conf:
            plugin_id = function_conf["plugin"]
            import karp.pluginmanager as plugins

            res = plugins.plugins[plugin_id].apply_plugin_function(
                src_resource.entity_id, src_resource.version, src_entry
            )
        else:
            raise NotImplementedError()
        return res

    def update_references(
        self,
        resource_id: str,
        # resource_repo: ResourceRepository,
        # indexer: SearchService,
        # resource: entities.Resource,
        entry_ids: typing.Iterable[str],
    ) -> None:
        add = collections.defaultdict(list)
        for src_entry_id in entry_ids:
            refs = self.get_referenced_entries.query(resource_id, src_entry_id)
            for field_ref in refs:
                ref_resource = self.resource_repo.get_by_resource_id(
                    field_ref.resource_id, version=(field_ref.resource_version)
                )
                if ref_resource:
                    ref_index_entry = self.transform(
                        # resource_repo,
                        # indexer,
                        ref_resource.resource_id,  # TODO use resource directly
                        field_ref.entry,
                        # ref_resource.config["fields"].items(),
                    )
                    # metadata = resourcemgr.get_metadata(ref_resource, field_ref["id"])
                    add[field_ref.resource_id].append(ref_index_entry)

        for ref_resource_id, ref_entries in add.items():
            self.index_uow.repo.add_entries(ref_resource_id, ref_entries)
