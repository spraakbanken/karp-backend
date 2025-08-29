import logging

from injector import inject
from sqlalchemy.orm import Session

import karp.plugins as plugins
from karp.lex.application import EntryQueries, ResourceQueries
from karp.plugins import Plugins
from karp.search.infrastructure.es.indices import EsIndex
from karp.search.infrastructure.transformers import entry_transformer

logger = logging.getLogger(__name__)


class SearchCommands:
    @inject
    def __init__(
        self,
        session: Session,
        index: EsIndex,
        resource_queries: ResourceQueries,
        entry_queries: EntryQueries,
        plugins: Plugins,
    ):
        super().__init__()
        self.session = session
        self.index = index
        self.resource_queries = resource_queries
        self.entry_queries = entry_queries
        self.plugins = plugins

    def reindex_resource(self, resource_id, remove_old_index):
        """
        Create a new index with the latest versions of all non-discarded entries. Check for changes
        done during reindex and loop until the new index and db are synced. Optionally remove the old index
        using remove_old_index and finally update the alias for resource_id to the new index.
        """
        logger.info("Reindexing resource '%s'", resource_id)
        resource = self.resource_queries.by_resource_id(resource_id, expand_plugins=plugins.INDEXED)

        # create and add data to new index without touching the old alias
        index_name = self.index.create_index(resource_id, resource.config, create_alias=False)

        from_timestamp = 0
        to_timestamp = self.entry_queries.get_max_last_modified(resource_id)

        # loop while updates that are not added to the new index are found
        while True:
            if from_timestamp != 0:
                # after the first iteration, there might be deletes of previously indexed entry
                removed_entries = self.entry_queries.deleted_entries(resource_id, last_modified=from_timestamp)
                logger.info("Syncing deletions to new index")
                errors = self.index.delete_entries(
                    index_name, entry_ids=(str(entry_id) for entry_id in removed_entries), raise_on_error=False
                )
                # an entry could be added AND deleted during reindex
                for error in errors:
                    logger.info(f"Something was probably added and deleted during reindex: {error}")
                logger.info("Syncing new additions/updates to new index")

            entries = self.entry_queries.all_entries(
                resource_id, last_modified=from_timestamp, expand_plugins=plugins.INDEXED
            )

            self.index.add_entries(index_name, (entry_transformer.transform(entry) for entry in entries))

            # before looking for changes, rollback the session to to start a new transaction
            self.session.rollback()
            new_timestamp = self.entry_queries.get_max_last_modified(resource_id)

            if to_timestamp != new_timestamp:
                logger.info("Something has changed during reindex, try again")
                from_timestamp = to_timestamp
                to_timestamp = new_timestamp
            else:
                break

        if remove_old_index:
            self.index.delete_index(resource_id)

        # now when the data adding is done, point alias to the new index
        self.index.create_alias(resource_id, index_name)
        logger.info("Reindexing done")

    def reindex_all_resources(self, remove_old_index):
        for resource in self.resource_queries.get_all_resources():
            self.reindex_resource(resource.resource_id, remove_old_index)
