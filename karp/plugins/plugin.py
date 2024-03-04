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

def transform_config(plugins: Plugins, resource_config: Dict) -> Dict:
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
    def transform_fields(config: Dict, path: list[Union[str, int]], body: Dict) -> Dict:
        result = {}
        for k, v in body.items():
            if k in config and not config[k].get("virtual"): # virtual is handled below
                result[k] = transform_field(config[k], path + [k], v)
            else:
                result[k] = v

        for field, field_config in config.items():
            if field_config.get("virtual"):
                result[field] = generate_virtual(field_config, path + [field])

        return result

    # TODO: do everything in-place so that recursive virtual fields work
    def transform_field(config: Dict, path: list[Union[str, int]], body: Dict) -> Dict:
        if config.get("collection"):
            flat_config = dict(config)
            del flat_config["collection"]
            return [transform_field(flat_config, path + [i], x)
                    for i, x in enumerate(body)]

        elif config["type"] == "object":
            return transform_fields(config["fields"], path, body)

        else:
            return body

    def resolve_field(path, arg):
        arg = list(arg.split("."))

        arg, body = find_common_path(path, arg, original_body)
        return select_field(arg, body)

    def find_common_path(path, arg, body):
        if path and isinstance(path[0], int):
            return find_common_path(path[1:], arg, body[path[0]])
        if path and arg and path[0] == arg[0]:
            return find_common_path(path[1:], arg[1:], body[path[0]])
        return arg, body

    def select_field(arg, body):
        if not arg:
            return body
        if isinstance(body, list):  # assume collection
            return [select_field(x, arg) for x in body]
        # TODO raise a proper exception
        assert isinstance(body, dict) and arg[0] in body  # noqa: S101
        return select_field(arg[1:], body[arg[0]])

    def generate_virtual(config: Dict, path: list[Union[str, int]]) -> Dict:
        field_params = {
            k: resolve_field(path, v)
            for k, v in config.get("field_params", {}).items()
        }

        # If any field_param is a list, call the plugin once per list element
        if any(isinstance(value, list) for value in field_params.values()):
            return [plugins.generate(config, **field_params_flat)
                    for field_params_flat in flatten_dict(field_params)]
        else:
            return plugins.generate(config, **field_params)

    def flatten_dict(d: Dict) -> Iterator[Dict]:
        for k, v in d.items():
            if isinstance(v, list):
                for item in v:
                    yield from flatten_dict(d | {k: item})
                break
        else:
            yield d

    config = transform_config(plugins, resource_config)
    return transform_fields(config["fields"], [], original_body)
