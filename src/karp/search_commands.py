import logging

import karp.plugins as plugins
from karp.globals import session
from karp.lex.application import entry_queries, resource_queries
from karp.search.infrastructure.es import indices as es_index
from karp.search.infrastructure.transformers import entry_transformer

logger = logging.getLogger(__name__)


def reindex_resource(resource_id, remove_old_index):
    """
    Create a new index with the latest versions of all non-discarded entries. Check for changes
    done during reindex and loop until the new index and db are synced. Optionally remove the old index
    using remove_old_index and finally update the alias for resource_id to the new index.
    """
    logger.info("Reindexing resource '%s'", resource_id)
    resource = resource_queries.by_resource_id(resource_id, expand_plugins=plugins.INDEXED)

    # create and add data to new index without touching the old alias
    index_name = es_index.create_index(resource_id, resource.config, call_create_alias=False)

    from_timestamp = 0
    to_timestamp = entry_queries.get_max_last_modified(resource_id)

    # loop while updates that are not added to the new index are found
    while True:
        if from_timestamp != 0:
            # after the first iteration, there might be deletes of previously indexed entry
            removed_entries = entry_queries.deleted_entries(resource_id, last_modified=from_timestamp)
            logger.info("Syncing deletions to new index")
            errors = es_index.delete_entries(
                index_name, entry_ids=(str(entry_id) for entry_id in removed_entries), raise_on_error=False
            )
            # an entry could be added AND deleted during reindex
            for error in errors:
                logger.info(f"Something was probably added and deleted during reindex: {error}")
            logger.info("Syncing new additions/updates to new index")

        entries = entry_queries.all_entries(resource_id, last_modified=from_timestamp, expand_plugins=plugins.INDEXED)

        es_index.add_entries(index_name, (entry_transformer.transform(entry) for entry in entries))

        # before looking for changes, rollback the session to to start a new transaction
        session.rollback()
        new_timestamp = entry_queries.get_max_last_modified(resource_id)

        if to_timestamp != new_timestamp:
            logger.info("Something has changed during reindex, try again")
            from_timestamp = to_timestamp
            to_timestamp = new_timestamp
        else:
            break

    if remove_old_index:
        es_index.delete_index(resource_id)

    # now when the data adding is done, point alias to the new index
    es_index.create_alias(resource_id, index_name)
    logger.info("Reindexing done")


def reindex_all_resources(remove_old_index):
    for resource in resource_queries.get_all_resources():
        reindex_resource(resource.resource_id, remove_old_index)
