import dataclasses

from injector import Injector

from karp.foundation.value_objects import unique_id


@dataclasses.dataclass
class UnitTestContext:
    injector: Injector


def ensure_correct_id_type(v) -> unique_id.UniqueId:
    try:
        return unique_id.UniqueId.validate(v)
    except ValueError as exc:
        raise ValueError(f"expected valid UniqueId, got '{v}' (type: `{type(v)}')") from exc
