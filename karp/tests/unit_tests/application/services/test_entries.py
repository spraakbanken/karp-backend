import pytest

from karp.application.services import entries


def test_entries_add_entries_wo_resource_raises():
    with pytest.raises(ValueError) as excinfo:
        entries.add_entries(None, None, None)

    assert (
        str(excinfo.value)
        == "'resource_id' must be of type 'str', were '<class 'NoneType'>'"
    )
