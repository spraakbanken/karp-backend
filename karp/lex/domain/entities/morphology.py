import abc
from typing import Any

from .resource import Resource


class Morphology(abc.ABC, Resource):
    @abc.abstractmethod
    def get_inflection_table(
        self, identifer: str, lemma: str, **kwargs
    ) -> list[dict[str, Any]]:
        ...
