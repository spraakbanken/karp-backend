import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from pprint import pp
from typing import Callable, Dict, Iterable, Iterator, Optional, Type, Union

from frozendict import deepfreeze
from graphlib import CycleError, TopologicalSorter
from injector import Injector, inject

from karp.foundation.cache import Cache
from karp.foundation.entry_points import entry_points
from karp.foundation.json import expand_path, get_path, localise_path, make_path, set_path

logger = logging.getLogger(__name__)


class PluginException(Exception):
    pass


class Plugin(ABC):
    @abstractmethod
    def output_config(**kwargs) -> Dict:
        raise NotImplementedError

    # Either generate or generate_batch should be implemented
    def generate_batch(self, batch) -> Iterable[Dict]:
        return [self.generate(**d) for d in batch]

    def generate(self, **kwargs) -> Dict:
        result = list(self.generate_batch([kwargs]))
        if len(result) != 1:
            raise AssertionError("generate_batch returned wrong number of results")
        return result[0]


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
        self.plugins = Cache(lambda name: injector.get(find_plugin(name)))

    def _get_plugin(self, config: Dict) -> Plugin:
        if "plugin" not in config:
            raise PluginException(f'Resource config has "virtual": "true" but no "plugin" field')
        return self.plugins[config["plugin"]]

    def output_config(self, config: Dict) -> Dict:
        return self._get_plugin(config).output_config(**config.get("params", {}))

    def generate(self, config: Dict, **kwargs) -> Dict:
        # TODO: turn into {"error": "plugin failed"} or whatever
        return self._get_plugin(config).generate(**config.get("params", {}), **kwargs)

    def generate_batch(self, config: Dict, batch) -> Iterable[Dict]:
        # TODO: turn into {"error": "plugin failed"} or whatever
        params = config.get("params", {})
        result = list(self._get_plugin(config).generate_batch([params | item for item in batch]))
        if len(result) != len(batch):
            raise AssertionError("batch result had wrong length")
        return result


# TODO: maybe these things should take EntryDto and ResourceDto and
# transform them?

# TODO: maybe a more descriptive name like expand instead of transform?


def transform_config(plugins: Plugins, resource_config: Dict) -> Dict:
    """Given a resource config with virtual fields, expand the config
    by adding the output_config for each virtual field."""

    def _transform_fields(config: Dict) -> Dict:
        return {k: _transform_field(v) for k, v in config.items()}

    def _transform_field(config: Dict):
        if config.get("virtual"):
            result = _transform_field(plugins.output_config(config))
            return config | result

        if config["type"] == "object":
            config = dict(config)
            config["fields"] = _transform_fields(config["fields"])

        return config

    result = dict(resource_config)
    result["fields"] = _transform_fields(resource_config["fields"])
    return result


def find_virtual_fields(resource_config: Dict) -> dict[str, Dict]:
    """Find all virtual fields declared in a resource_config."""

    result = {}

    def _search_fields(path: list[str], config: Dict):
        for field, value in config.items():
            _search_field(path + [field], value)

    def _search_field(path: list[str], config: Dict):
        if config.get("virtual"):
            result[".".join(path)] = config

        elif config["type"] == "object":
            _search_fields(path, config["fields"])

    _search_fields([], resource_config["fields"])
    return result


def transform(plugins: Plugins, resource_config: Dict, body: Dict) -> Dict:
    """
    Given an entry body, calculate all the virtual fields.
    """

    return transform_many(plugins, resource_config, [body])[0]


def transform_many(plugins: Plugins, resource_config: Dict, bodies: list[Dict]) -> list[Dict]:
    """
    Given a list of entry bodies, calculate all the virtual fields.
    """

    # TODO: support references to collections which should be passed in as lists

    resource_config = transform_config(plugins, resource_config)
    bodies = deepcopy(bodies)
    virtual_fields = find_virtual_fields(resource_config)

    def generate_batch(config: Dict, batch: list) -> Iterator:
        """Calculate the value for a batch of virtual fields."""

        # In the simple case we can just call plugins.generate_batch.
        # But here the tricky bit is: If any field_param is a list,
        # we should invoke the plugin once per list element.

        # First compute all needed plugin invocations (we use a dict to remove
        # duplicates - can't use a set because flat_field_params isn't hashable)
        batch_dict = {}
        for field_params in batch:
            for flat_field_params in select_from_dict(field_params):
                batch_dict[deepfreeze(flat_field_params)] = flat_field_params

        # Execute the batch query and make a map 'invocation -> result'
        batch_result_list = plugins.generate_batch(config, batch_dict.values())
        batch_result = dict(zip(batch_dict, batch_result_list))

        # Now look up the results
        for field_params in batch:
            if any(isinstance(value, list) for value in field_params.values()):
                yield [
                    batch_result[deepfreeze(flat_field_params)]
                    for flat_field_params in select_from_dict(field_params)
                ]
            else:
                yield batch_result[deepfreeze(field_params)]

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
        for target_name in config.get("field_params", {}).values():
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

    # Decide what order to compute the virtual fields in
    try:
        order = list(TopologicalSorter(dependencies).static_order())
    except CycleError:
        raise PluginError(f"virtual fields form a cycle: {e.args[1]}") from None

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
        batch = [
            {
                k: get_path(localise_path(v, pos), bodies[i])
                for k, v in config.get("field_params", {}).items()
            }
            for i, pos in occurrences
        ]

        # Execute the plugin on the batch and store the result
        batch_result = generate_batch(virtual_fields[field_name], batch)
        for (i, pos), result in zip(occurrences, batch_result):
            set_path(pos, result, bodies[i])

    return bodies
