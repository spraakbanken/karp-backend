import typing

import pydantic
from karp.foundation import unit_of_work


class IndexEntry(pydantic.BaseModel):  # noqa: D101
    id: str  # noqa: A003
    entry: typing.Dict

    def __bool__(self) -> bool:  # noqa: D105
        return bool(self.entry)


class IndexUnitOfWork(unit_of_work.UnitOfWork):  # noqa: D101
    pass
