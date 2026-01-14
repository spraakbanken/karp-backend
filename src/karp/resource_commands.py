import logging

from karp import plugins
from karp.foundation.timings import utc_now
from karp.globals import session
from karp.lex.domain import entities, errors
from karp.lex.domain.dtos import ResourceDto
from karp.lex.domain.errors import IntegrityError, ResourceNotFound
from karp.lex.infrastructure.sql import resource_repository
from karp.main.errors import KarpError
from karp.search.infrastructure.es import indices as es_index

logger = logging.getLogger(__name__)


def create_resource(config, user):
    resource_id = config.resource_id
    existing_resource = resource_repository.by_resource_id_optional(resource_id)
    if existing_resource and not existing_resource.discarded:
        raise IntegrityError(f"Resource with resource_id='{resource_id}' already exists.")

    resource = entities.create_resource(
        config=config,
        message=f"Resource '{resource_id}' created.",
        created_at=utc_now(),
        created_by=user,
    )

    # check an entry schema can be generated from the config
    try:
        _ = resource.entry_schema
    except errors.InvalidEntrySchema as e:
        raise KarpError("Cannot create entry schema from the given config.") from None

    resource_repository.save(resource)
    config = plugins.transform_config(resource.config, expand_plugins=plugins.INDEXED)
    es_index.create_index(resource.resource_id, config)
    session.commit()
    return ResourceDto.from_resource(resource)


def update_resource(resource_id, version, config, message, user):
    resource = resource_repository.by_resource_id(resource_id)
    updated = resource.update(
        config=config,
        user=user,
        message=message,
        timestamp=utc_now(),
        version=version,
    )
    if updated:
        resource_repository.save(resource)
    session.commit()


def publish_resource(resource_id, message, user, version):
    logger.info("publishing resource", extra={"resource_id": resource_id})
    resource = resource_repository.by_resource_id(resource_id)
    if not resource:
        raise ResourceNotFound(resource_id)
    resource.publish(
        user=user,
        message=message,
        timestamp=utc_now(),
        version=version,
    )
    resource_repository.save(resource)
    session.commit()


def unpublish_resource(resource_id, user, version, keep_index=False):
    logger.info("unpublishing resource", extra={"resource_id": resource_id})
    resource = resource_repository.by_resource_id(resource_id)
    if not resource.is_published:
        return False
    resource.unpublish(user=user, version=version)
    resource_repository.save(resource)
    session.commit()
    if not keep_index:
        es_index.delete_index(resource_id)
    return True


def delete_resource(resource_id):
    resource = resource_repository.by_resource_id(resource_id)
    if not resource:
        return False

    # delete the index with alias "resource_id" from Elasticsearch
    es_index.delete_index(resource_id)

    # drop resource table
    resource = resource_repository.by_resource_id(resource_id)
    resource_repository.remove_resource_table(resource)

    # delete all rows from resource table associated with resource_id
    resource_repository.delete_all_versions(resource_id)
    session.commit()
    return True
