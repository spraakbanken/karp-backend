"""The resource config."""

from typing import Any, Optional

import pydantic

from karp.foundation import alias_generators


class BaseModel(pydantic.BaseModel):
    model_config = {
        "frozen": True,  # since changes won't be saved to the database anyway
        "extra": "forbid",
        "alias_generator": alias_generators.to_lower_camel,
        "populate_by_name": True,
    }

    @classmethod
    def from_str(cls, config_str):
        return cls.model_validate_json(config_str)

    @classmethod
    def from_file(cls, filename):
        with open(filename) as fp:
            return cls.from_str(fp.read())

    def update(self, **kwargs: dict[str, Any]):
        updated = self.model_copy(update=kwargs)
        return updated.model_validate(updated.model_dump())


class ResourceConfig(BaseModel):
    fields: dict[str, "Field"]
    sort: Optional[str | list[str]] = None  # TODO what does it mean if it's a list?
    protected: dict[str, bool] = {}
    id: Optional[str] = None
    additional_properties: bool = True

    @classmethod
    def from_dict(cls, config):
        config = dict(config)
        if "resource_id" in config:
            del config["resource_id"]
        if "resource_name" in config:
            del config["resource_name"]
        return cls.model_validate(config)


class Field(BaseModel):
    # TODO split this up into one class per type, to allow for better validation
    type: Optional[str] = None  # required except for virtual fields
    required: bool = False
    collection: bool = False
    virtual: bool = False
    plugin: Optional[str] = None
    params: dict[str, Any] = {}
    field_params: dict[str, str] = {}
    fields: Optional[dict[str, "Field"]] = None
    skip_raw: Optional[bool] = False  # for strings only
    additional_properties: bool = True


def parse_create_resource_config(config: dict[str, Any]):
    try:
        resource_id = config.pop("resource_id")
    except KeyError as exc:
        raise ValueError("'resource_id' is missing") from exc
    name = config.pop("resource_name", None)

    return resource_id, name, ResourceConfig.model_validate(config)
