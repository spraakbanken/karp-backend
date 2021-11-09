import collections
import logging
import typing

from karp.lex.domain import entities
from karp.lex.application.queries import GetReferencedEntries
from karp.lex.application.repositories import ResourceUnitOfWork, EntryUowRepositoryUnitOfWork
from karp.search.application.transformers import EntryTransformer
from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.search.domain import search_service


logger = logging.getLogger("karp")


class GenericEntryTransformer(EntryTransformer):
    def __init__(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
        get_referenced_entries: GetReferencedEntries,
    ) -> None:
        super().__init__()
        self.search_service_uow = search_service_uow
        self.resource_uow = resource_uow
        self.entry_uow_repo_uow = entry_uow_repo_uow
        self.get_referenced_entries = get_referenced_entries

    def _get_resource(self, resource_id: str) -> entities.Resource:
        with self.resource_uow as uw:
            return uw.repo.by_resource_id(resource_id)

    def transform(self, resource_id: str, src_entry: entities.Entry) -> search_service.IndexEntry:
        """
        TODO This is very slow (for resources with references) because of db-lookups everywhere in the code
        TODO We can pre-fetch the needed entries (same code that only looks for refs?) or
        TODO somehow get the needed entries in bulk after transforming some entries and insert them into
        TODO the transformed entries afterward. Very tricky.
        """
        print(f"transforming entry_id={src_entry.entry_id}")
        search_service_entry = self.search_service_uow.repo.create_empty_object()
        search_service_entry.id = src_entry.entry_id
        self.search_service_uow.repo.assign_field(
            search_service_entry, "_entry_version", src_entry.version)
        self.search_service_uow.repo.assign_field(
            search_service_entry, "_last_modified", src_entry.last_modified
        )
        self.search_service_uow.repo.assign_field(
            search_service_entry, "_last_modified_by", src_entry.last_modified_by
        )
        resource = self._get_resource(resource_id=resource_id)
        self._transform_to_index_entry(
            resource,
            # resource_repo,
            # search_serviceer,
            src_entry.body,
            search_service_entry,
            resource.config["fields"].items(),
        )
        return search_service_entry

    def _transform_to_index_entry(
        self,
        resource: entities.Resource,
        # resource_repo: ResourceRepository,
        # search_serviceer: SearchService,
        _src_entry: typing.Dict,
        _search_service_entry: search_service.IndexEntry,
        fields,
    ):
        for field_name, field_conf in fields:
            if field_conf.get("virtual"):
                print("found virtual field")
                res = self._evaluate_function(
                    field_conf["function"], _src_entry, resource)
                print(f"res = {res}")
                if res:
                    self.search_service_uow.repo.assign_field(
                        _search_service_entry, "v_" + field_name, res)
            elif field_conf.get("ref"):
                ref_field = field_conf["ref"]
                if ref_field.get("resource_id"):
                    ref_resource = self.resource_uow.repo.by_resource_id(
                        ref_field["resource_id"], version=ref_field["resource_version"]
                    )
                    # if not ref_resource:
                    #     raise errors.ResourceNotFoundError(
                    #         ref_field["resource_id"], ref_field["resource_version"]
                    #     )
                    if ref_field["field"].get("collection"):
                        ref_objs = []
                        if ref_resource:
                            for ref_id in _src_entry[field_name]:
                                with self.entry_uow_repo_uow.get_by_id(
                                    ref_resource.entry_repository_id
                                ) as ref_resource_entries_uw:
                                    ref_entry_body = (
                                        ref_resource_entries_uw.repo.by_entry_id(
                                            str(ref_id)
                                        )
                                    )
                                    ref_resource_entries_uw.commit()
                                if ref_entry_body:
                                    ref_entry = {
                                        field_name: ref_entry_body.body}
                                    ref_search_service_entry = (
                                        self.search_service_uow.repo.create_empty_object()
                                    )
                                    list_of_sub_fields = (
                                        (field_name, ref_field["field"]),)
                                    self._transform_to_index_entry(
                                        resource,
                                        # resource_repo,
                                        # search_serviceer,
                                        ref_entry,
                                        ref_search_service_entry,
                                        list_of_sub_fields,
                                    )
                                    ref_objs.append(
                                        ref_search_service_entry.entry[field_name])
                        self.search_service_uow.repo.assign_field(
                            _search_service_entry, "v_" + field_name, ref_objs
                        )
                    else:
                        raise NotImplementedError()
                else:
                    ref_id = _src_entry.get(field_name)
                    if not ref_id:
                        continue
                    if not ref_field["field"].get("collection", False):
                        ref_id = [ref_id]

                    for elem in ref_id:
                        with self.entry_uow_repo_uow.get_by_id(
                            resource.entry_repository_id
                        ) as resource_entries_uw:
                            ref = resource_entries_uw.repo.by_entry_id(
                                str(elem))
                            resource_entries_uw.commit()
                        if ref:
                            ref_entry = {field_name: ref.body}
                            ref_search_service_entry = self.search_service_uow.repo.create_empty_object()
                            list_of_sub_fields = (
                                (field_name, ref_field["field"]),)
                            self._transform_to_index_entry(
                                resource,
                                # resource_repo,
                                # search_serviceer,
                                ref_entry,
                                ref_search_service_entry,
                                list_of_sub_fields,
                            )
                            self.search_service_uow.repo.assign_field(
                                _search_service_entry,
                                "v_" + field_name,
                                ref_search_service_entry.entry[field_name],
                            )

            if field_conf["type"] == "object":
                print("found field with type 'object'")
                field_content = self.search_service_uow.repo.create_empty_object()
                if field_name in _src_entry:
                    self._transform_to_index_entry(
                        resource,
                        # resource_repo,
                        # search_serviceer,
                        _src_entry[field_name],
                        field_content,
                        field_conf["fields"].items(),
                    )
            else:
                field_content = _src_entry.get(field_name)

            if field_content:
                self.search_service_uow.repo.assign_field(
                    _search_service_entry, field_name, field_content)

    def _evaluate_function(
        self,
        # resource_repo: ResourceRepository,
        # search_serviceer: SearchService,
        function_conf: typing.Dict,
        src_entry: typing.Dict,
        src_resource: entities.Resource,
    ):
        print(
            f"search_serviceing._evaluate_function src_resource={src_resource.resource_id}")
        print(f"search_serviceing._evaluate_function src_entry={src_entry}")
        if "multi_ref" in function_conf:
            function_conf = function_conf["multi_ref"]
            target_field = function_conf["field"]
            if "resource_id" in function_conf:
                print(
                    f"search_serviceing._evaluate_function: trying to find '{function_conf['resource_id']}'"
                )
                target_resource = self.resource_uow.repo.by_resource_id(
                    function_conf["resource_id"], version=function_conf["resource_version"]
                )
                if target_resource is None:
                    logger.warning(
                        "Didn't find the resource with resource_id='%s'",
                        function_conf["resource_id"],
                    )
                    return self.search_service_uow.repo.create_empty_list()
            else:
                target_resource = src_resource
            print(
                f"search_serviceing._evaluate_function target_resource={target_resource.resource_id}"
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
                    with self.entry_uow_repo_uow.get_by_id(
                        target_resource.entry_repository_id
                    ) as target_entries_uw:
                        target_entries = target_entries_uw.repo.by_referenceable(
                            filters)
                else:
                    raise NotImplementedError()
            else:
                raise NotImplementedError()

            res = self.search_service_uow.repo.create_empty_list()
            for entry in target_entries:
                search_service_entry = self.search_service_uow.repo.create_empty_object()
                list_of_sub_fields = (("tmp", function_conf["result"]),)
                self._transform_to_index_entry(
                    target_resource,
                    # resource_repo,
                    # search_serviceer,
                    {"tmp": entry.body},
                    search_service_entry,
                    list_of_sub_fields,
                )
                self.search_service_uow.repo.add_to_list_field(
                    res, search_service_entry.entry["tmp"])
        elif "plugin" in function_conf:
            plugin_id = function_conf["plugin"]
            import karp.pluginmanager as plugins

            res = plugins.plugins[plugin_id].apply_plugin_function(
                src_resource.id, src_resource.version, src_entry
            )
        else:
            raise NotImplementedError()
        return res

    def update_references(
        self,
        resource_id: str,
        # resource_repo: ResourceRepository,
        # search_serviceer: SearchService,
        # resource: entities.Resource,
        entry_ids: typing.Iterable[str],
    ) -> None:
        add = collections.defaultdict(list)
        with self.resource_uow:
            for src_entry_id in entry_ids:
                refs = self.get_referenced_entries.query(
                    resource_id, src_entry_id
                )
                for field_ref in refs:
                    ref_resource_id = field_ref["resource_id"]
                    ref_resource = self._get_resource(
                        ref_resource_id,
                        version=(field_ref["resource_version"])
                    )
                    if ref_resource:
                        ref_search_service_entry = self.transform_to_search_service_entry(
                            # resource_repo,
                            # search_serviceer,
                            ref_resource,
                            field_ref["entry"],
                            # ref_resource.config["fields"].items(),
                        )
                        # metadata = resourcemgr.get_metadata(ref_resource, field_ref["id"])
                        add[ref_resource_id].append(ref_search_service_entry)

        for ref_resource_id, ref_entries in add.items():
            self.search_service_uow.repo.add_entries(ref_resource_id, ref_entries)
