from karp.domain.models.entry import Entry, EntryOp, EntryStatus

from karp.utility import unique_id


class MorphologicalEntry(Entry):
    def __init__(
        self,
        *pos,
        **kwargs
    ):
        super().__init__(*pos, **kwargs)


def create_morphological_entry(
    entry_id: str
) -> MorphologicalEntry:
    return MorphologicalEntry(
        entity_id=unique_id.make_unique_id(),
        entry_id=entry_id,
        body={},
        message="",
        op=EntryOp.ADDED,
        status=EntryStatus.IN_PROGRESS,
        version=1,
    )
