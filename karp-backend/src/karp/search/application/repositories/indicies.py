import typing

import pydantic


class IndexEntry(pydantic.BaseModel):  # noqa: D101
    id: str  # noqa: A003
    entry: typing.Dict

    def __bool__(self) -> bool:  # noqa: D105
        return bool(self.entry)
