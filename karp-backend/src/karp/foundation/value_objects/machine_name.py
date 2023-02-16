import pydantic  # noqa: D100


class MachineName(pydantic.BaseModel):  # noqa: D101
    name: str
