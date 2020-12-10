from typing import List, Tuple

from paradigmextract import morphparser

from karp.domain.models.entry import Entry, EntryOp, EntryStatus

from karp.utility import unique_id


class MorphologicalEntry(Entry):
    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.paradigm = None
        self.tags = ()

    
    def get_inflection_table(self, wordform: str) -> List[Tuple[str, str]]:
        # for now, assume wordform is the baseform
        variables = morphparser.eval_baseform(self.paradigm, wordform, self.tags)
        if variables is None:
            return []
        res = []
        table = self.paradigm(*variables)
        for form, msd in table:
            res.append((msd, form))
            if not msd:
                # when can this happend?
                res.append((None, form))
        return res


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
