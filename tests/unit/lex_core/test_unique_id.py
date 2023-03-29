from datetime import datetime

import pytest
from karp.lex_core.value_objects import UniqueId, make_unique_id


def test_unique_ids_are_sortable():  # noqa: ANN201
    assert make_unique_id() > make_unique_id(datetime(1999, 12, 31))


class TestUniqueId:
    def test_bad_tyoe_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            UniqueId.validate(None)

    def test_bad_input_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            UniqueId.validate("not-an-ulid")
