import typing

import pydantic


class IndexEntry(pydantic.BaseModel):
    id: str
    entry: typing.Dict

    def __bool__(self) -> bool:
        return bool(self.entry)
