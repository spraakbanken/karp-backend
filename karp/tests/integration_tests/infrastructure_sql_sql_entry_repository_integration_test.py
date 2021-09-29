import pytest

from karp.domain.errors import NonExistingField
from karp.infrastructure.sql.sql_entry_repository import SqlEntryRepository
from karp.infrastructure.unit_of_work import unit_of_work
from karp.tests import common_data


def test_by_referenceable_w_nonexisting_field_raises():
    repo = SqlEntryRepository.from_dict(
        {"table_name": "places", "config": common_data.CONFIG_PLACES}
    )

    with pytest.raises(NonExistingField) as exc_info:
        with unit_of_work(using=repo) as uw:
            uw.by_referenceable(nonexisting=1)

    assert str(exc_info.value) == "Field 'nonexisting' doesn't exist."
