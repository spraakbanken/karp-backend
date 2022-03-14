import pydantic


class MachineName(pydantic.BaseModel):
    name: str
