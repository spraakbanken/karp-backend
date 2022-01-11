import pytest

from karp.domain.models.entry import EntryRepository, create_entry
from karp.domain.models.resource import create_resource
from karp.infrastructure.sql import sql_entry_repository
from karp.infrastructure.unit_of_work import unit_of_work
from karp.tests import common_data

# from tests.integration_tests.common_fixtures import fixture_places


def test_places_has_entry_repository(places):
    assert isinstance(places.entry_repository, EntryRepository)
    with unit_of_work(using=places.entry_repository) as uw:
        assert len(uw.entry_ids()) == 0


def test_places_search_by_referenceable(places):
    assert isinstance(places.entry_repository, EntryRepository)
    with unit_of_work(using=places.entry_repository) as uw:
        for entry_dict in common_data.PLACES:
            entry = create_entry(str(entry_dict["code"]), entry_dict)
            uw.put(entry)
        uw.commit()

        assert len(uw.entry_ids()) == 9

        entry_copies = uw.by_referenceable(larger_place=7)

        assert len(entry_copies) == 1
        entry_copy = entry_copies[0]

        assert entry_copy.entry_id == "1"

        # print(f"...= {uw.by_referenceable(municipality=1)}")
        assert len(uw.by_referenceable(municipality=1)) == 2
        assert len(uw.by_referenceable(municipality=2)) == 6
        assert len(uw.by_referenceable(municipality=3)) == 6
