import pytest

from karp.domain.models.entry import EntryRepository, create_entry
from karp.domain.models.resource import create_resource
from karp.infrastructure.sql import sql_entry_repository
from karp.infrastructure.unit_of_work import unit_of_work


@pytest.fixture
def resource_blam():
    resource = create_resource(
        {
            "resource_id": "blam",
            "resource_name": "Blam",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "id": "baseform",
        }
    )

    yield resource

    resource.entry_repository.teardown()


def test_resource_has_entry_respository(resource_blam):

    assert isinstance(resource_blam.entry_repository, EntryRepository)
    with unit_of_work(using=resource_blam.entry_repository) as uw:
        assert len(uw.entry_ids()) == 0


def test_resource_put_entry(resource_blam):

    assert isinstance(resource_blam.entry_repository, EntryRepository)

    with unit_of_work(using=resource_blam.entry_repository) as uw:
        entry = create_entry("hubba", {})
        uw.put(entry)
        uw.commit()

        entry_ids = uw.entry_ids()
        assert len(entry_ids) == 1
        assert "hubba" in entry_ids
