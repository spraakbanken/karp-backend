from typing import Iterable, Optional

from karp import plugins
from karp.lex.domain.dtos import ResourceDto
from karp.lex.domain.entities import Resource
from karp.lex.infrastructure.sql import resource_repository

"""Implements various queries about the resource list, giving answers as DTO.
Used for example in resources_api.py.

For now the API is a subset of resource_repository, but returning DTOs."""


def _from_resource(resource: Resource, expand_plugins=True) -> ResourceDto:
    return plugins.transform_resource(ResourceDto.from_resource(resource), expand_plugins=expand_plugins)


def by_resource_id(resource_id: str, version: Optional[int] = None, **kwargs) -> ResourceDto:
    result = resource_repository.by_resource_id(resource_id, version=version)
    return _from_resource(result, **kwargs)


def by_resource_id_optional(resource_id: str, version: Optional[int] = None, **kwargs) -> Optional[ResourceDto]:
    result = resource_repository.by_resource_id_optional(resource_id, version=version)
    if result is not None:
        return _from_resource(result, **kwargs)


def get_published_resources(**kwargs) -> Iterable[ResourceDto]:
    return [_from_resource(r, **kwargs) for r in resource_repository.get_published_resources()]


def get_all_resources(**kwargs) -> Iterable[ResourceDto]:
    return [_from_resource(r, **kwargs) for r in resource_repository.get_all_resources()]
