import abc
import typing

import pydantic

from karp.foundation import repository, unit_of_work


class IndexEntry(pydantic.BaseModel):
    id: str
    entry: typing.Dict

    def __bool__(self) -> bool:
        return bool(self.entry)


class Index(repository.Repository[IndexEntry]):
    @abc.abstractmethod
    def create_index(self, resource_id: str, config: typing.Dict):
        pass

    @abc.abstractmethod
    def publish_index(self, resource_id: str):
        pass

    @abc.abstractmethod
    def add_entries(self, resource_id: str, entries: typing.Iterable[IndexEntry]):
        pass

    @abc.abstractmethod
    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: typing.Optional[str] = None,
    ):
        pass

    def create_empty_object(self) -> IndexEntry:
        return IndexEntry(id="", entry={})

    def assign_field(self, _index_entry: IndexEntry, field_name: str, part):
        if isinstance(part, IndexEntry):
            part = part.entry
        _index_entry.entry[field_name] = part

    def create_empty_list(self) -> typing.List:
        return []

    def add_to_list_field(self, elems: typing.List, elem):
        if isinstance(elem, IndexEntry):
            elem = elem.entry
        elems.append(elem)

    def _save(self, _notused):
        pass

    def _by_id(self, id) -> None:
        return None

    def num_entities(self) -> int:
        raise NotImplementedError("num_entities is not used for indicies")


class IndexUnitOfWork(unit_of_work.UnitOfWork[Index]):
    pass
