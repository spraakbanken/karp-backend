import abc  # noqa: D100, I001
import typing

import pydantic

from karp.foundation import repository, unit_of_work


class IndexEntry(pydantic.BaseModel):  # noqa: D101
    id: str  # noqa: A003
    entry: typing.Dict

    def __bool__(self) -> bool:  # noqa: D105
        return bool(self.entry)


class Index(repository.Repository[IndexEntry]):  # noqa: D101
    @abc.abstractmethod
    def create_index(self, resource_id: str, config: typing.Dict):  # noqa: ANN201, D102
        pass

    @abc.abstractmethod
    def publish_index(self, resource_id: str):  # noqa: ANN201, D102
        pass

    @abc.abstractmethod
    def add_entries(  # noqa: ANN201, D102
        self, resource_id: str, entries: typing.Iterable[IndexEntry]
    ):
        pass

    @abc.abstractmethod
    def delete_entry(  # noqa: ANN201, D102
        self,
        resource_id: str,
        *,
        entry_id: typing.Optional[str] = None,
    ):
        pass

    def create_empty_object(self) -> IndexEntry:  # noqa: D102
        return IndexEntry(id="", entry={})

    def assign_field(  # noqa: ANN201, D102
        self, _index_entry: IndexEntry, field_name: str, part
    ):
        if isinstance(part, IndexEntry):
            part = part.entry
        _index_entry.entry[field_name] = part

    def create_empty_list(self) -> typing.List:  # noqa: D102
        return []

    def add_to_list_field(self, elems: typing.List, elem):  # noqa: ANN201, D102
        if isinstance(elem, IndexEntry):
            elem = elem.entry
        elems.append(elem)

    def _save(self, _notused):  # noqa: ANN202
        pass

    def _by_id(self, id) -> None:  # noqa: A002
        return None

    def num_entities(self) -> int:  # noqa: D102
        raise NotImplementedError("num_entities is not used for indicies")


class IndexUnitOfWork(unit_of_work.UnitOfWork[Index]):  # noqa: D101
    pass
