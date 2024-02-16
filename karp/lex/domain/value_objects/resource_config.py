import pydantic  # noqa: D100


class ResourceConfig(pydantic.BaseModel):  # noqa: D101
    fields: dict
