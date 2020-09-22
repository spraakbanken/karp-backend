from typing import Dict
from uuid import uuid4
from karp.domain.models.entry import EntryRepository
from unittest import mock
import uuid

import pytest

from karp.domain.errors import ConsistencyError, DiscardedEntityError, ConstraintsError
from karp.domain.models.lexical_resource import LexicalResource
from karp.domain.models.resource import (
    Resource,
    ResourceOp,
    Release,
)


def create_resource(resource_id: str, name: str, config: Dict) -> LexicalResource:
    entry_repository_mock = mock.MagicMock(
        spec=EntryRepository, type="repository_type", id=uuid4()
    )
    with mock.patch("karp.utility.time.utc_now", return_value=12345), mock.patch(
        "karp.domain.models.entry.EntryRepository.get_default_repository_type",
        return_value="repository_type",
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create_repository_settings",
        return_value={},
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create",
        return_value=entry_repository_mock,
    ):
        resource = Resource.create_resource("lexical_resource", config)

    return resource


def test_resource_create_resource_creates_lexical_resource():
    resource_id = "test_resource"
    name = "Test resource"
    conf = {
        "resource_id": resource_id,
        "resource_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    entry_repository_mock = mock.MagicMock(
        spec=EntryRepository, type="repository_type", id=uuid4()
    )
    with mock.patch("karp.utility.time.utc_now", return_value=12345), mock.patch(
        "karp.domain.models.entry.EntryRepository.get_default_repository_type",
        return_value="repository_type",
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create_repository_settings",
        return_value={},
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create",
        return_value=entry_repository_mock,
    ):
        resource = Resource.create_resource("lexical_resource", conf)

    assert isinstance(resource, Resource)
    assert isinstance(resource, LexicalResource)
    assert resource.type == "lexical_resource"
    assert LexicalResource.type == "lexical_resource"
    assert resource.id == uuid.UUID(str(resource.id), version=4)
    assert resource.version == 1
    assert resource.resource_id == resource_id
    assert resource.name == name
    assert not resource.discarded
    assert not resource.is_published
    assert "resource_id" not in resource.config
    assert "resource_name" not in resource.config
    assert "entry_repository_type" in resource.config
    # assert "entry_repository_settings" in resource.config
    assert "sort" in resource.config
    assert resource.config["sort"] == conf["sort"]
    assert "fields" in resource.config
    assert resource.config["fields"] == conf["fields"]
    assert int(resource.last_modified) == 12345
    assert resource.message == "Resource added."
    assert resource.op == ResourceOp.ADDED
    assert resource.entry_repository is not None
    assert isinstance(resource.entry_repository, EntryRepository)
    assert resource.entry_repository_id == resource.entry_repository.id
    assert resource.entry_repository_type == "repository_type"


def test_lexical_resource_stamp_changes_last_modified_and_version():
    resource_id = "test_resource"
    name = "Test resource"
    conf = {
        "resource_id": resource_id,
        "resource_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
        "entry_repository_type": None,
        "entry_repository_settings": {},
    }
    resource = create_resource(resource_id, name, conf)

    previous_last_modified = resource.last_modified
    previous_version = resource.version

    resource.stamp(user="Test")

    assert resource.last_modified > previous_last_modified
    assert resource.last_modified_by == "Test"
    assert resource.version == (previous_version + 1)


def test_lexical_resource_add_new_release_creates_release():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )

    previous_last_modified = resource.last_modified

    resource.add_new_release(name="v1.0.0", user="Admin", description="")

    assert len(resource.releases) == 1
    assert resource.releases[0].name == "v1.0.0"
    assert resource.releases[0].publication_date == resource.last_modified
    assert resource.releases[0].description == ""
    assert resource.releases[0].root.id == resource.id
    assert resource.last_modified > previous_last_modified
    assert resource.last_modified_by == "Admin"
    assert resource.message == "Release 'v1.0.0' created."
    assert resource.version == 2


def test_lexical_resource_release_with_name_on_discarded_raises_discarded_entity_error():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )

    resource.discard(user="Test", message="Discard")

    assert resource.discarded

    with pytest.raises(DiscardedEntityError):
        resource.release_with_name("test")


def test_lexical_resource_add_new_release_on_discarded_raises_discarded_entity_error():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )

    resource.discard(user="Test", message="Discard")

    assert resource.discarded

    with pytest.raises(DiscardedEntityError):
        resource.add_new_release(name="test", user="TEST", description="")


def test_lexical_resource_add_new_release_with_invalid_name_raises_constraints_error():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )

    with pytest.raises(ConstraintsError):
        resource.add_new_release(name="", user="Test", description="")


def test_lexical_resource_new_release_added_with_wrong_version_raises_consistency_error():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )
    event = Resource.NewReleaseAdded(
        entity_id=resource.id,
        entity_version=12,
    )
    with pytest.raises(ConsistencyError):
        event.mutate(resource)


def test_lexical_resource_new_release_added_with_wrong_last_modified_raises_consistency_error():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )
    event = Resource.NewReleaseAdded(
        entity_id=resource.id, entity_version=resource.version, entity_last_modified=2
    )
    with pytest.raises(ConsistencyError):
        event.mutate(resource)


def test_lexical_release_created_has_id():
    release = Release(
        entity_id="e", name="e-name", publication_date=12345.0, description="ee"
    )

    assert release.id == "e"
    assert release.name == "e-name"
    assert release.publication_date == 12345.0
    assert release.description == "ee"
    assert release.root.id == release.id


def test_lexical_release_created_w_resource_has_id():
    resource = create_resource(
        "test_resource",
        "Test resource",
        {
            "resource_id": "test_resource",
            "resource_name": "Test resource",
            "sort": ["baseform"],
            "fields": {"baseform": {"type": "string", "required": True}},
            "entry_repository_type": None,
            "entry_repository_settings": {},
        },
    )
    release = Release(
        entity_id="e",
        name="e-name",
        publication_date=12345.0,
        description="ee",
        aggregate_root=resource,
    )

    assert release.id == "e"
    assert release.name == "e-name"
    assert release.publication_date == 12345.0
    assert release.description == "ee"
    assert release.root.id == resource.id


def test_lexical_resource_with_entry_repository_settings():
    conf = {
        "resource_id": "test_id_4",
        "resource_name": "a",
        "entry_repository_type": "test_type",
        "entry_repository_settings": {"settings": "test"},
    }
    entry_repository_mock = mock.MagicMock(
        spec=EntryRepository, type="test_type", id=uuid4()
    )
    with mock.patch("karp.utility.time.utc_now", return_value=12345), mock.patch(
        "karp.domain.models.entry.EntryRepository.get_default_repository_type",
        return_value="repository_type",
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create_repository_settings",
        return_value={},
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create",
        return_value=entry_repository_mock,
    ):
        resource = Resource.create_resource("lexical_resource", conf)
    # with mock.patch(
    #     "karp.domain.models.entry.EntryRepository", spec=EntryRepository
    # ) as entry_repository_cls_mock:
    #     entry_repository_mock = mock.MagicMock(autospec=EntryRepository)
    #     entry_repository_mock.type.return_value == "test_type"
    #     entry_repository_cls_mock.return_value = entry_repository_mock
    #     resource = Resource.create_resource("lexical_resource", conf)

    assert resource.entry_repository.type == "test_type"
    assert resource.entry_repository_id == resource.entry_repository.id


def test_lexical_resource_with_entry_repository_id():
    entry_repository_id = uuid4()
    conf = {
        "resource_id": "test_id_4",
        "resource_name": "a",
        "entry_repository_id": entry_repository_id,
        "entry_repository_type": "test_type",
    }
    entry_repository_mock = mock.MagicMock(
        spec=EntryRepository, type="test_type", id=uuid4()
    )
    with mock.patch("karp.utility.time.utc_now", return_value=12345), mock.patch(
        "karp.domain.models.entry.EntryRepository.get_default_repository_type",
        return_value="repository_type",
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.create_repository_settings",
        return_value={},
    ), mock.patch(
        "karp.domain.models.entry.EntryRepository.repository",
        # return_value=entry_repository_mock,
    ) as entry_repository_repository_mock:
        entry_repository_repository_mock.by_id.return_value = entry_repository_mock
        resource = Resource.create_resource("lexical_resource", conf)
    # with mock.patch(
    #     "karp.domain.models.entry.EntryRepository", spec=EntryRepository
    # ) as entry_repository_cls_mock:
    #     entry_repository_mock = mock.MagicMock(autospec=EntryRepository)
    #     entry_repository_mock.type.return_value == "test_type"
    #     entry_repository_cls_mock.return_value = entry_repository_mock
    #     resource = Resource.create_resource("lexical_resource", conf)

    assert resource.entry_repository.type == "test_type"
    assert resource.entry_repository_id == resource.entry_repository.id
