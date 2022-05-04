from typing import Any

from karp.lex.domain.entities import Morphology


class SmdbMorphology(Morphology):
    def get_inflection_table(
        self, identifer: str, lemma: str, **kwargs
    ) -> list[dict[str, Any]]:
        return super().get_inflection_table(identifer, lemma, **kwargs)
