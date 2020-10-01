import pytest

from karp.domain.services import entries


def test_entries_add_entries_wo_resource_raises():
    with pytest.raises(ValueError) as excinfo:
        entries.add_entries(None, None)

    assert "Must provide resource" in str(excinfo.value)
