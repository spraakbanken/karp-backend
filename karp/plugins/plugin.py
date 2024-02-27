from abc import ABC, abstractmethod
from typing import Dict, Type
from injector import Injector, inject
from pprint import pp


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
        return self._get_plugin(config).generate(**config.get("params", {}), **kwargs)

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

def transform(plugins: Plugins, resource_config: Dict, body: Dict) -> Dict:
    def _resolve_field(path, bodies, arg):
        path = list(path)
        arg = list(arg.split("."))
        prefix = []
        while path and arg and path[0] == arg[0]:
            prefix.append(path[0])
            path.pop(0)
            arg.pop(0)

        return _select_field(arg, bodies[tuple(prefix)])

    def _select_field(arg, body):
        if not arg: return body
        if isinstance(body, list): # assume collection
            return [_select_field(x, arg) for x in body]
        # TODO raise a proper exception
        assert isinstance(body, dict) and arg[0] in body
        return _select_field(arg[1:], body[arg[0]])

    def _transform_fields(config: Dict, path: tuple[str], bodies: Dict[tuple[str], Dict]) -> Dict:
        result = {}
        for k, v in bodies[path].items():
            if k in config:
                bodies[path + (k,)] = v
                result[k] = _transform_field(config[k], path + (k,), bodies)
                del bodies[path + (k,)]
            else:
                result[k] = v

        for field, field_config in config.items():
            if field_config.get("virtual"):
                field_params = {k: _resolve_field(path, bodies, v)
                          for k, v in field_config.get("field_params", {}).items()}
                result[field] = plugins.generate(field_config, **field_params)

        return result

    def _transform_field(config: Dict, path: tuple[str], bodies: Dict[tuple[str], Dict]):
        if config.get("collection"):
            flat_config = dict(config)
            del flat_config["collection"]
            result = []
            for x in bodies[path]:
                bodies[path] = x
                result.append(_transform_field(flat_config, path, bodies))
            return result

        elif config["type"] == "object":
            return _transform_fields(config["fields"], path, bodies)

        else:
            return bodies[path]

    config = transform_config(plugins, resource_config)
    return _transform_fields(config["fields"], (), {(): body})

