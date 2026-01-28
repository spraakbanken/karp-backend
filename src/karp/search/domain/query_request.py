import logging
from dataclasses import dataclass, field

from karp.search.domain.highlight_param import HighlightParam
from karp.search.domain.query_dsl.karp_query_model import ModelBase

logger = logging.getLogger(__name__)


@dataclass
class QueryRequest:
    resources: list[str]
    q: str | ModelBase = ""
    from_: int = 0
    size: int | None = 25
    lexicon_stats: bool = True
    highlight: HighlightParam = field(default_factory=lambda: HighlightParam.false)
    sort: list[str] = field(default_factory=list)
    path: str | None = None

    def __post_init__(self) -> None:
        # if resources is provided as a comma-separated string, split it.
        if isinstance(self.resources, str):
            self.resources = [s for s in self.resources.split(",") if s]
