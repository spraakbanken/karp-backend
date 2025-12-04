"""The resource config."""

from typing import Any, Optional

import pydantic
import yaml

from karp.foundation import alias_generators
from karp.foundation.json import Path, make_path


class BaseModel(pydantic.BaseModel):
    model_config = {
        "frozen": True,  # since changes won't be saved to the database anyway
        "extra": "forbid",
        "alias_generator": alias_generators.to_lower_camel,
        "populate_by_name": True,
    }

    def update(self, **kwargs: dict[str, Any]):
        updated = self.model_copy(update=kwargs)
        return updated.model_validate(updated.model_dump())


class ResourceConfig(BaseModel):
    resource_id: str
    resource_name: Optional[str] = None
    fields: dict[str, "Field"]
    plugins: dict[str, dict[str, str]] = {}
    sort: Optional[str | list[str]] = None  # TODO what does it mean if it's a list?
    protected: dict[str, bool] = {}
    id: Optional[str] = None
    additional_properties: bool = True
    config_str: str

    @classmethod
    def from_str(cls, config_str, extra=None):
        # If the config file is in JSON format, it might use tab
        # characters, which are not allowed in YAML 1.1.
        # This can be removed once PyYAML supports YAML 1.2.
        config_str = config_str.replace("\t", " ")

        config_dict = yaml.load(config_str, Loader=yaml.CSafeLoader)
        config_dict["config_str"] = config_str
        if extra:
            config_dict.update(extra)
        return cls.model_validate(config_dict)

    @classmethod
    def from_path(cls, path) -> "ResourceConfig":
        with open(path) as fp:
            return cls.from_str(fp.read())

    @classmethod
    def from_dict(cls, config_dict):
        config_str = yaml.dump(config_dict, Dumper=yaml.CDumper)
        return cls.from_str(config_str)

    def nested_fields(self):
        for field, config in self.fields.items():
            yield from config.nested_fields([field])

    def entry_field_config(self) -> "Field":
        """Return a Field config for a whole entry considered as a JSON object."""

        return Field(
            type="object",
            required=True,
            additional_properties=self.additional_properties,
            fields=self.fields,
        )

    def field_config(self, path: str | Path) -> "Field":
        """
        Return a Field config for a given path, according to what
        would be returned by get_path.
        """

        required = True

        field = self.entry_field_config()
        for component in make_path(path):
            if field.type != "object" or component not in field.fields:
                raise ValueError(f"Path {path} not found in config")

            field = field.fields[component]

        return field

    def nesting_level(self, path: str | Path) -> int:
        """
        Given a path, calculate how many levels of nested lists are
        returned by a call to get_path. For example, a collection
        inside of another collection has a nesting level of 2.
        """

        result = 0
        field = self.entry_field_config()
        for component in make_path(path):
            field = field.fields[component]
            if field.collection:
                result += 1

        return result


class Field(BaseModel):
    # TODO split this up into one class per type, to allow for better validation
    type: Optional[str] = None  # required except for virtual fields
    required: bool = False
    collection: bool = False
    virtual: bool = False
    plugin: Optional[str] = None
    params: dict[str, Any] = {}
    field_params: dict[str, str | list[str]] = {}
    fields: Optional[dict[str, "Field"]] = None
    hidden: bool = False  # only for virtual fields at the moment
    flatten_params: bool = False
    allow_missing_params: bool = False
    cache_plugin_expansion: bool = True
    searchable: bool = True  # only for virtual fields at the moment
    skip_raw: Optional[bool] = False  # for strings only
    additional_properties: bool = True

    def nested_fields(self, prefix):
        yield ".".join(prefix)
        if self.type == "object":
            for field, config in self.fields.items():
                yield from config.nested_fields(prefix + [field])
