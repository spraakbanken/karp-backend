from typing import Any, List, Tuple

from paradigmextract import morphparser
from paradigmextract import paradigm as pe_paradigm

from karp.domain.models.entry import Entry, EntryOp, EntryStatus
from karp.domain.value_objects import unique_id


class MorphologicalEntry(Entry):
    def __init__(
        self,
        *args,
        form_msds: List[Tuple[str, Any]],
        var_insts: List[List[Tuple[str, Any]]],
        pos: str,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.paradigm = pe_paradigm.Paradigm(
            form_msds=form_msds,
            var_insts=var_insts,
            p_id=self.entry_id,
            pos=pos,
            uuid=self.id,
        )
        self.tags = ("inf aktiv", "inf s-form") if pos in ["vb", "vbm"] else ()

    def get_inflection_table(self, wordform: str) -> List[Tuple[str, str]]:
        # for now, assume wordform is the baseform
        variables = morphparser.eval_baseform(
            self.paradigm,
            wordform,
            self.tags,
        )
        print(f"variables = {variables}")
        if variables is None:
            print("early exit")
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
    entry_id: str,
    *,
    pos: str,
    form_msds: List[Tuple[str, Any]],
    var_insts: List[List[Tuple[str, Any]]],
    resource_id: str,
) -> MorphologicalEntry:
    return MorphologicalEntry(
        entity_id=unique_id.make_unique_id(),
        entry_id=entry_id,
        resource_id=resource_id,
        body={},
        message="",
        op=EntryOp.ADDED,
        status=EntryStatus.IN_PROGRESS,
        version=1,
        form_msds=form_msds,
        var_insts=var_insts,
        pos=pos,
    )
