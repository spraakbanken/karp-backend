import pydantic


class ResourceConfig(pydantic.BaseModel):
    fields: dict
