import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from pprint import pp
from typing import Callable, Dict, Iterable, Iterator, Optional, Type, Union

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

    # TODO: support references to collections which should be passed in as lists

    resource_config = transform_config(plugins, resource_config)
    virtual_fields = find_virtual_fields(resource_config)
    body = deepcopy(body)

    def generate_virtual(config: Dict, pos: list[Union[str, int]]) -> Dict:
        """Calculate the value for a virtual field."""

        field_params = {
            k: get_path(localise_path(v, pos), body)
            for k, v in config.get("field_params", {}).items()
        }

        # If any field_param is a list, call the plugin once per list element
        if any(isinstance(value, list) for value in field_params.values()):
            return [
                plugins.generate(config, **selection)
                for selection in select_from_dict(field_params)
            ]
        else:
            return plugins.generate(config, **field_params)

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
        occurrences = expand_path(parent_path, body)

        for parent_pos in occurrences:
            field_pos = parent_pos + [field_path[-1]]
            value = generate_virtual(virtual_fields[field_name], field_pos)
            set_path(field_pos, value, body)

    return body
