import logging
from typing import Any

from injector import inject

from karp.lex.application import SearchQueries
from karp.lex.application.resource_queries import ResourceQueries
from karp.search.domain import QueryRequest
from karp.search.domain.query_dsl.karp_query_model import Identifier, TextArgExpression

from .plugin import INDEXED, Plugin, group_batch_by

logger = logging.getLogger(__name__)


class BacklinkPlugin(Plugin):
    """
    A plugin that find all references to a entry via a target field
    For example:
    - a resource has a field called thing_id and ref_field
    - ref_field can contain values that occur in thing_id (typically a ID of some sort)
    - a virtual field with BacklinkPlugin for thing_id should contain all entries that have the value of thing_id in ref_field

    This plugin adds the link data during fetching in the API and is not available for search.
    """

    @inject
    def __init__(self, resources: ResourceQueries, search_queries: SearchQueries):
        self.search_queries = search_queries
        self.resources = resources

    def output_config(self, resource, field, *args, **kwargs):
        """
        Note that currently the relationship is assumed to be one-to-many or many-to-many
        """
        # lookup <field> in the <resource> and check its type
        resource_dto = self.resources.by_resource_id_optional(resource, expand_plugins=False)
        if not resource_dto:
            logger.warning(
                f'The linked resource "{resource}", does not exist. '
                "Reindex this resource after it has been added to make backlinks work."
            )
            return {"type": "object", "fields": {}}
        field_type = resource_dto.config.fields[field].type
        return {
            "type": field_type,
            "collection": True,
            "searchable": False,
        }

    @group_batch_by("resource", "field", "target")
    def generate_batch(self, resource: str, field: str, target: Any, batch: list[dict[str, str]]):
        """
        target is the referencing field in other entry, used in the query to get the referees
        field is the name of identifying field for the reference, used to populate the backlink field
        """
        # collect all the ids and run one multi_query to find all of them
        all_ids = [item["id"] for item in batch]

        requests = [
            QueryRequest(
                resources=[resource],
                q=TextArgExpression(op="equals", field=Identifier(ast=target), arg=id),
                lexicon_stats=False,
                size=None,
            )
            for id in all_ids
        ]
        query_results = self.search_queries.multi_query(requests, expand_plugins=INDEXED)

        id_references = {
            id: [entry["entry"][field] for entry in entries["hits"]]
            for id, entries in zip(all_ids, query_results, strict=False)
        }

        # now collect the results
        result = [id_references.get(id, []) for id in all_ids]
        return result
