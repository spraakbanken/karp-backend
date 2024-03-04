from abc import ABC, abstractmethod
from pprint import pp
from typing import Dict, Type, Union, Iterator

from injector import Injector, inject


class Plugin(ABC):
    @classmethod
    def name(cls) -> str:
        # Take class name, remove "Plugin" suffix and convert
        # ThingsLikeThis to things_like_this
        name = cls.__name__.removesuffix("Plugin")

        def transform_char(i, c):
            if c.isupper():
                c = c.lower()
                if i != 0:
                    c = "_" + c
            return c

        return "".join([transform_char(i, c) for i, c in enumerate(name)])

    @abstractmethod
    def output_config(**kwargs) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def generate(**kwargs) -> Dict:
        raise NotImplementedError

    # TODO: bulk generate


plugin_registry: list[Type[Plugin]] = []


def register_plugin(plugin: Type[Plugin]):
    plugin_registry.append(plugin)


class Plugins:
    @inject
    def __init__(self, injector: Injector):
        self.plugins = {plugin.name(): injector.get(plugin) for plugin in plugin_registry}

    def _get_plugin(self, config: Dict) -> Plugin:
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
            result.update(config)
            return result

        if config["type"] == "object":
            config = dict(config)
            config["fields"] = _transform_fields(config["fields"])

        return config

    result = dict(resource_config)
    result["fields"] = _transform_fields(resource_config["fields"])
    return result


def transform(plugins: Plugins, resource_config: Dict, original_body: Dict) -> Dict:
    """Given an entry body, calculate all the virtual fields."""

    # Notes on some design decisions:
    #
    # 1. field_params and collection fields
    #
    # In Salex, the resource config defines the SOLemman field with {"collection": "true"}
    # which means that it is really a list of items. Imagine now that we have a virtual
    # field "extra_info" (not inside SOLemman) with a field_param referencing
    # SOLemman.s_nr. What does that mean? After all, the SOLemman field is a list, not an
    # object with an s_nr field.
    #
    # We say that SOLemman.s_nr gives a list of s_nrs, one for each SOLemman entry:
    # [SOLemman[0].s_nr, SOLemman[1].s_nr, ...]. The value of the field_param is then this
    # list of s_nrs. When running the plugin, we run it once for each item in the list,
    # generating a list of results. So the final value of "extra_info" is a list, with one
    # item per item in SOLemman. In general, when a field_param refers to a collection,
    # the virtual field ends up being a collection, with one item per value of the
    # field_param.
    #
    # But there is a complication. What if the virtual field is inside SOLemman, so it's
    # not "extra_info" but "SOLemman.extra_info"? Now suppose we are inside SOLemman[0]
    # and calculating SOLemman[0].extra_info. Then the field_param SOLemman.s_nr probably
    # shouldn't mean the list of all s_nrs! It should probably mean the s_nr for the
    # SOLemman object we're currently working on, i.e. SOLemman[0].s_nr.
    #
    # We handle this with a bit of a trick. When going through the entry, we maintain a
    # variable pos: list[Union[str, int]] which records where we are in the entry, e.g. if
    # we are inside SOLemman[1].lexem[3] then pos=["SOLemman", 1, "lexem", 3]. When
    # resolving a field_name, we can use the pos parameter to figure out that e.g.
    # SOLemman.l_nr "means" SOLemman[1].l_nr by matching the field_param with the pos.

    # TODO: support references to collections which should be passed in as lists

    def transform_fields(config: Dict, pos: list[Union[str, int]], body: Dict) -> Dict:
        result = {}
        # First transform the fields that currently exist in the body
        for k, v in body.items():
            if k in config and not config[k].get("virtual"): # virtual is handled below
                result[k] = transform_field(config[k], pos + [k], v)
            else:
                result[k] = v

        # Now add all the virtual fields from the config
        for field, field_config in config.items():
            if field_config.get("virtual"):
                result[field] = generate_virtual(field_config, pos + [field])

        return result

    # TODO: do everything in-place so that recursive virtual fields work
    def transform_field(config: Dict, pos: list[Union[str, int]], body: Dict) -> Dict:
        if config.get("collection"):
            flat_config = dict(config)
            del flat_config["collection"]
            return [transform_field(flat_config, pos + [i], x)
                    for i, x in enumerate(body)]

        elif config["type"] == "object":
            return transform_fields(config["fields"], pos, body)

        else:
            return body

    def generate_virtual(config: Dict, pos: list[Union[str, int]]) -> Dict:
        """Calculate the value for a virtual field."""

        field_params = {
            k: get_field(v.split("."), pos)
            for k, v in config.get("field_params", {}).items()
        }

        # If any field_param is a list, call the plugin once per list element
        if any(isinstance(value, list) for value in field_params.values()):
            return [plugins.generate(config, **selection)
                    for selection in select_from_dict(field_params)]
        else:
            return plugins.generate(config, **field_params)

    def get_field(field: list[str], pos: list[Union[str, int]]=None, body=original_body):
        """Get the value for a field_param. See comments at top of function transform."""

        if not field:
            assert not pos
            return body

        if isinstance(body, dict):
            # field[0] tells us which field to access.
            if pos and pos[0] != field[0]:
                # field and pos refer to different subfields so we should ignore pos
                pos = []

            return get_field(field[1:], pos[1:], body[field[0]])

        else:
            assert isinstance(body, list)

            # pos[0] tells us which field to access.
            if pos:
                return get_field(field, pos[1:], body[pos[0]])
            else:
                return [get_field(field, pos, x) for x in body]

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

    config = transform_config(plugins, resource_config)
    return transform_fields(config["fields"], [], original_body)
