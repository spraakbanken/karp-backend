import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from functools import wraps
from typing import Callable, Dict, Iterable, Iterator, Optional, Type

import methodtools
from fastapi import APIRouter
from frozendict import deepfreeze
from graphlib import CycleError, TopologicalSorter
from injector import Injector, inject

from karp.foundation.batch import batch_items
from karp.foundation.entry_points import entry_points
from karp.foundation.json import (
    del_path,
    expand_path,
    get_path,
    has_path,
    localise_path,
    make_path,
    set_path,
)
from karp.lex.domain.dtos import EntryDto, ResourceDto
from karp.lex.domain.value_objects import Field, ResourceConfig

logger = logging.getLogger(__name__)


class PluginException(Exception):
    pass


class Plugin(ABC):
    @abstractmethod
    def output_config(**kwargs) -> dict[str, Field]:
        raise NotImplementedError

    # Either generate or generate_batch should be implemented
    def generate_batch(self, batch) -> Iterable[Dict]:
        return [self.generate(**d) for d in batch]

    def generate(self, **kwargs) -> Dict:
        result = list(self.generate_batch([kwargs]))
        if len(result) != 1:
            raise AssertionError("generate_batch returned wrong number of results")
        return result[0]

    def create_router(self, resource_id: str, params: dict[str, str]) -> APIRouter:
        raise NotImplementedError()


def group_batch_by(*args):
    """
    A decorator to help with writing generate_batch. Collects batches
    into "sub-batches" and invokes generate_batch once on each sub-batch.

    Example: if batch items look like this:
        {"resource": "salex", "field": "ortografi", "other": "xx"}
    Then you can define:
        @group_batch_by("resource", "field")
        def generate_batch(self, resource, field, batch):
          ...
    The batch will be split into sub-batches, one sub-batch for each
    combination of "resource" and "field". Notice that "resource" and
    "field" become parameters to generate_batch. These fields are also
    removed from "batch", so the batch items will look like this:
        {"other": "xx"}
    """

    def batch_key(batch_item):
        return {arg: batch_item[arg] for arg in args}

    def batch_rest(batch_item):
        return {arg: batch_item[arg] for arg in batch_item if arg not in args}

    def inner(function):
        @wraps(function)
        def generate_batch(self, batch):
            batch = list(batch)

            # split the batch into sub-batches that all have the same key
            unfrozen_keys = {}
            sub_batches = defaultdict(dict)
            for i, item in enumerate(batch):
                frozen_key = str(batch_key(item))
                if frozen_key not in unfrozen_keys:
                    unfrozen_keys[frozen_key] = batch_key(item)

                sub_batches[frozen_key][i] = batch_rest(item)

            # run the plugin on all sub-batches
            results = {}
            for frozen_key, items in sub_batches.items():
                key = unfrozen_keys[frozen_key]
                sub_batch_results = list(function(self, **key, batch=list(items.values())))

                if len(sub_batch_results) != len(items):
                    raise AssertionError("size mismatch")

                for i, result in zip(items, sub_batch_results):
                    results[i] = result

            return [results[i] for i in range(len(batch))]

        return generate_batch

    return inner


plugin_registry: dict[str, Callable[[], Type[Plugin]]] = {}


def register_plugin(name: str, plugin: Type[Plugin]):
    plugin_registry[name] = lambda: plugin


def register_plugin_entry_point(entry_point):
    def load_plugin():
        logger.info("Loading plugin '%s'", entry_point.name)
        cls = entry_point.load()
        register_plugin(entry_point.name, cls)
        return cls

    plugin_registry[entry_point.name] = load_plugin


for entry_point in entry_points("karp.plugin"):
    register_plugin_entry_point(entry_point)


def find_plugin(name: str) -> Type[Plugin]:
    if name in plugin_registry:
        return plugin_registry[name]()
    else:
        raise PluginException(f"Plugin {name} not found")


class Plugins:
    @inject
    def __init__(self, injector: Injector):
        self.injector = injector

    @methodtools.lru_cache(maxsize=None)
    def _get_plugin(self, name: str) -> Plugin:
        if not name:
            raise PluginException('Resource config has "virtual": "true" but no "plugin" field')
        return self.injector.get(find_plugin(name))

    def register_routes(self, resources: Iterable[ResourceDto]):
        """
        Check if any resource has declared a plugin on top-level and register that plugin's routes
        """
        from karp.api.routes import router

        for resource in resources:
            for plugin_name, plugin_params in resource.config.plugins.items():
                inner_router = self._get_plugin(plugin_name).create_router(resource.resource_id, plugin_params)
                router.include_router(inner_router, prefix=f"/{resource.resource_id}/{plugin_name}")

    def output_config(self, config: Field) -> Field:
        result = self._get_plugin(config.plugin).output_config(**config.params)
        return Field.model_validate(dict(result))

    def generate(self, config: Field, **kwargs) -> Dict:
        # TODO: turn into {"error": "plugin failed"} or whatever
        return self._get_plugin(config.plugin).generate(**config.params, **kwargs)

    def generate_batch(self, config: Field, batch) -> Iterable[Dict]:
        # TODO: turn into {"error": "plugin failed"} or whatever
        batch = list(batch)
        if not batch:
            return []
        result = list(self._get_plugin(config.plugin).generate_batch(config.params | item for item in batch))
        if len(result) != len(batch):
            raise AssertionError("batch result had wrong length")
        return result


# TODO: maybe a more descriptive name like expand instead of transform?


def transform_resource(plugins: Plugins, resource_dto: "ResourceDto") -> "ResourceDto":
    """Given a resource with virtual fields, expand the config
    by adding the output_config for each virtual field."""

    result = resource_dto.model_copy(deep=True)
    result.config = transform_config(plugins, result.config)
    return result


def transform_config(plugins: Plugins, resource_config: ResourceConfig) -> ResourceConfig:
    """Given a resource config with virtual fields, expand the config
    by adding the output_config for each virtual field."""

    def _transform_fields(config: dict[str, Field]) -> dict[str, Field]:
        return {k: _transform_field(v) for k, v in config.items()}

    def _transform_field(config: Field):
        if config.virtual:
            result = _transform_field(plugins.output_config(config))
            # take some values from the input config too
            result = result.update(
                collection=config.collection or result.collection,
                required=config.required or result.required,
                virtual=True,
                hidden=config.hidden or result.hidden,
                plugin=config.plugin,
                params=config.params,
                field_params=config.field_params,
                flatten_params=config.flatten_params or result.flatten_params,
                allow_missing_params=config.allow_missing_params or result.allow_missing_params,
                cache_plugin_expansion=config.cache_plugin_expansion and result.cache_plugin_expansion,
            )
            return result

        if config.type == "object":
            return config.update(fields=_transform_fields(config.fields))

        return config

    result = resource_config.update(fields=_transform_fields(resource_config.fields))
    return result


def find_virtual_fields(resource_config: ResourceConfig) -> dict[str, Field]:
    """Find all virtual fields declared in a resource_config."""

    result = {}
    for name in resource_config.nested_fields():
        field = resource_config.field_config(name)
        if field.virtual:
            result[name] = field

    return result


def transform_entry(plugins: Plugins, resource_config: ResourceConfig, entry_dto: "EntryDto") -> "EntryDto":
    """
    Given an entry, calculate all the virtual fields.
    """

    return next(iter(transform_entries(plugins, resource_config, [entry_dto])))


def transform_entries(
    plugins: Plugins, resource_config: ResourceConfig, entry_dtos: Iterable["EntryDto"]
) -> Iterator["EntryDto"]:
    """
    Given a list of entries, calculate all the virtual fields.
    """

    cached_results = {}
    for batch in batch_items(entry_dtos, max_batch_size=10000):
        new_entries = transform_list(plugins, resource_config, [entry_dto.entry for entry_dto in batch], cached_results)
        for entry_dto, new_entry in zip(batch, new_entries):
            entry_dto = entry_dto.model_copy(deep=True)
            entry_dto.entry = new_entry
            yield entry_dto


def transform(plugins: Plugins, resource_config: ResourceConfig, body: Dict) -> Dict:
    """
    Given an entry body, calculate all the virtual fields.
    """

    return next(iter(transform_list(plugins, resource_config, [body])))


def transform_list(
    plugins: Plugins,
    resource_config: ResourceConfig,
    bodies: list[Dict],
    cached_results: Optional[Dict] = None,
) -> list[Dict]:
    """
    Given a list of entry bodies, calculate all the virtual fields.

    cached_results is an optional parameter which allows for caching plugin
    results across multiple calls to transform_list. Use it like this:

    cached_results = {}                  # create cache once
    transform_list(..., cached_results)  # use it in several calls to transform_list
    transform_list(..., cached_results)
    transform_list(..., cached_results)
    """

    # TODO: support references to collections which should be passed in as lists

    if cached_results is None:
        cached_results = {}

    resource_config = transform_config(plugins, resource_config)
    bodies = deepcopy(bodies)
    virtual_fields = find_virtual_fields(resource_config)

    def generate_batch(config: Field, batch: list) -> Iterator:
        """Calculate the value for a batch of virtual fields."""

        nonlocal cached_results

        # In the simple case we can just call plugins.generate_batch.
        # But here the tricky bit is: If any field_param is a list,
        # we should invoke the plugin once per list element.

        # First compute all needed plugin invocations (we use a dict to remove
        # duplicates - can't use a set because flat_field_params isn't hashable)

        outer_cache_key = config.model_dump_json()
        if outer_cache_key not in cached_results:
            cached_results[outer_cache_key] = {}
        inner_cached_results = cached_results[outer_cache_key]

        def cache_key(flat_field_params):
            if config.cache_plugin_expansion:
                return deepfreeze(flat_field_params)
            else:
                return id(flat_field_params)

        batch_dict = {}
        for field_params in batch:
            for flat_field_params in select_from_dict(field_params) if config.flatten_params else [field_params]:
                key = cache_key(flat_field_params)
                if key not in inner_cached_results:
                    batch_dict[key] = flat_field_params

        # Execute the batch query and store the results into cached_results
        batch_result_list = plugins.generate_batch(config, batch_dict.values())
        results = dict(zip(batch_dict, batch_result_list))

        if config.cache_plugin_expansion:
            inner_cached_results |= results
            results = inner_cached_results

        # Now look up the results
        for field_params in batch:
            if config.flatten_params and any(isinstance(value, list) for value in field_params.values()):
                yield [results[cache_key(flat_field_params)] for flat_field_params in select_from_dict(field_params)]
            else:
                yield results[cache_key(field_params)]

    def select_from_dict(d: Dict) -> Iterator[Dict]:
        """Flatten a dict-of-lists into an iterator-of-dicts.

        >>> for x in select_from_dict({'x': [1,2], 'y': [3,[4,5]], 'z': 6}): print(x)
        {'x': 1, 'y': 3, 'z': 6}
        {'x': 1, 'y': 4, 'z': 6}
        {'x': 1, 'y': 5, 'z': 6}
        {'x': 2, 'y': 3, 'z': 6}
        {'x': 2, 'y': 4, 'z': 6}
        {'x': 2, 'y': 5, 'z': 6}
        """

        for k, v in d.items():
            if isinstance(v, list):
                for item in v:
                    yield from select_from_dict(d | {k: item})
                break
        else:
            yield d

    # Compute dependencies for the fields
    dependencies: Dict[str, set[str]] = {}
    for field_name, config in virtual_fields.items():
        # In order for the virtual field to appear in the topological sort (below),
        # it must exist in the dependencies graph, even if it has no dependencies
        dependencies[field_name] = set()

        # Dependencies through field_params
        for target_list in config.field_params.values():
            for target_name in flatten_list(target_list):
                if target_name in virtual_fields:
                    dependencies[field_name].add(target_name)

        # Dependencies through one field being a child of another
        # (can happen when a virtual field creates its own virtual subfields)
        for ancestor_name in virtual_fields:
            if field_name != ancestor_name:
                field_path = make_path(field_name)
                ancestor_path = make_path(ancestor_name)

                if field_path[: len(ancestor_path)] == ancestor_path:
                    dependencies[field_name].add(ancestor_name)

    # Check that all fields exist
    for targets in dependencies.values():
        for field_name in targets:
            if field_name not in resource_config.nested_fields():
                raise PluginException(f"field {field_name} not found")

    # Decide what order to compute the virtual fields in
    try:
        order = list(TopologicalSorter(dependencies).static_order())
    except CycleError as e:
        raise PluginException(f"virtual fields form a cycle: {e.args[1]}") from None

    # Expand each field in turn
    for field_name in order:
        field_path = make_path(field_name)
        parent_path = field_path[:-1]

        # Find all occurrences of the field
        occurrences = [
            (i, parent_pos + [field_path[-1]])
            for i, body in enumerate(bodies)
            for parent_pos in expand_path(parent_path, body)
        ]

        # Generate a batch of all needed field_params values
        batch = []
        batch_occurrences = []

        for i, pos in occurrences:
            field_params = {}
            for k, v in virtual_fields[field_name].field_params.items():

                def get_field_param(param):
                    if isinstance(param, list):
                        result = [get_field_param(p) for p in param]
                        if not virtual_fields[field_name].allow_missing_params:  # noqa: B023
                            result = [val for val in result if val is not None]
                        return result
                    else:
                        path = localise_path(param, pos)  # noqa: B023
                        if not has_path(path, bodies[i]):  # noqa: B023
                            return None
                        else:
                            return get_path(path, bodies[i])  # noqa: B023

                val = get_field_param(v)

                # Skip field if include_if value is False
                if k == "include_if":
                    if not val:
                        break

                else:
                    if not virtual_fields[field_name].allow_missing_params and val is None:
                        break
                    field_params[k] = val

            else:
                batch_occurrences.append((i, pos))
                batch.append(field_params)

        # Execute the plugin on the batch and store the result
        batch_result = generate_batch(virtual_fields[field_name], batch)
        for (i, pos), result in zip(batch_occurrences, batch_result):
            set_path(pos, result, bodies[i])

    # Delete any hidden fields
    for field_name, config in virtual_fields.items():
        if config.hidden:
            for body in bodies:
                for path in expand_path(field_name, body):
                    del_path(path, body)

    return bodies


def flatten_list(x):
    if isinstance(x, list):
        for y in x:
            yield from flatten_list(y)
    else:
        yield x
