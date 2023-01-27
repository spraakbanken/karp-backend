import copy
import uuid
from unittest import mock

import pytest

from karp.lex.domain import errors, events
from karp.lex.domain.errors import (
    ConsistencyError,
    ConstraintsError,
    DiscardedEntityError,
)
from karp.lex.domain.entities.resource import (
    Release,
    Resource,
    ResourceOp,
    create_resource,
)
from karp.foundation.value_objects import unique_id

from . import factories
from .factories import random_resource


def test_create_resource_creates_resource():
    resource_id = "test_resource"
    name = "Test resource"
    conf = {
        "resource_id": resource_id,
        "resource_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    with mock.patch("karp.utility.time.utc_now", return_value=12345):
        resource = create_resource(
            conf,
            created_by="kristoff@example.com",
            entry_repo_id=unique_id.make_unique_id(),
        )

    assert isinstance(resource, Resource)
    assert isinstance(resource.entity_id, unique_id.UniqueIdType)
    assert resource.entity_id == unique_id.parse(str(resource.entity_id))
    assert resource.version == 1
    assert resource.resource_id == resource_id
    assert resource.name == name
    assert not resource.discarded
    assert not resource.is_published
    assert "resource_id" not in resource.config
    assert "resource_name" not in resource.config
    assert "sort" in resource.config
    assert resource.config["sort"] == conf["sort"]
    assert "fields" in resource.config
    assert resource.config["fields"] == conf["fields"]
    assert int(resource.last_modified) == 12345
    assert resource.message == "Resource added."
    assert resource.op == ResourceOp.ADDED
    assert resource.domain_events[-1] == events.ResourceCreated(
        timestamp=resource.last_modified,
        entity_id=resource.id,
        entry_repo_id=resource.entry_repository_id,
        resource_id=resource.resource_id,
        name=resource.name,
        config=resource.config,
        user=resource.last_modified_by,
        message=resource.message,
    )


def test_resource_update_changes_last_modified_and_version():
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

    resource = factories.ResourceFactory(
        name=copy.deepcopy(name), config=copy.deepcopy(conf)
    )
    previous_last_modified = resource.last_modified
    previous_version = resource.version

    conf["fields"]["new"] = {"type": "string"}
    resource.update(name="new name", config=conf, user="Test", version=1)

    assert resource.last_modified > previous_last_modified
    assert resource.last_modified_by == "Test"
    assert resource.version == (previous_version + 1)
    assert resource.domain_events[-1] == events.ResourceUpdated(
        timestamp=resource.last_modified,
        entity_id=resource.id,
        entry_repo_id=resource.entry_repository_id,
        resource_id=resource.resource_id,
        name=resource.name,
        config=resource.config,
        user=resource.last_modified_by,
        message=resource.message,
        version=resource.version,
    )


# def test_resource_add_new_release_creates_release():
#     resource = factories.ResourceFactory()

#     previous_last_modified = resource.last_modified

#     resource.add_new_release(name="v1.0.0", user="Admin", description="")

#     assert len(resource.releases) == 1
#     assert resource.releases[0].name == "v1.0.0"
#     assert resource.releases[0].publication_date == resource.last_modified
#     assert resource.releases[0].description == ""
#     assert resource.releases[0].root.id == resource.id
#     assert resource.last_modified > previous_last_modified
#     assert resource.last_modified_by == "Admin"
#     assert resource.message == "Release 'v1.0.0' created."
#     assert resource.version == 2


# def test_resource_release_with_name_on_discarded_raises_discarded_entity_error():
#     resource = factories.ResourceFactory()

#     resource.discard(user="Test", message="Discard")

#     assert resource.discarded

#     with pytest.raises(DiscardedEntityError):
#         resource.release_with_name("test")


# def test_resource_add_new_release_on_discarded_raises_discarded_entity_error():
#     resource = factories.ResourceFactory()

#     resource.discard(user="Test", message="Discard")

#     assert resource.discarded

#     with pytest.raises(DiscardedEntityError):
#         resource.add_new_release(name="test", user="TEST", description="")


# @pytest.mark.skip()
# def test_resource_add_new_release_with_invalid_name_raises_constraints_error():
#     resource = factories.ResourceFactory()

#     with pytest.raises(ConstraintsError):
#         resource.add_new_release(name="", user="Test", description="")


# @pytest.mark.skip()
# def test_resource_new_release_added_with_wrong_version_raises_consistency_error():
#     resource = factories.ResourceFactory()
#     event = Resource.NewReleaseAdded(
#         entity_id=resource.id,
#         entity_version=12,
#     )
#     with pytest.raises(ConsistencyError):
#         event.mutate(resource)


# @pytest.mark.skip()
# def test_resource_new_release_added_with_wrong_last_modified_raises_consistency_error():
#     resource = factories.ResourceFactory()
#     event = Resource.NewReleaseAdded(
#         entity_id=resource.id, entity_version=resource.version, entity_last_modified=2
#     )
#     with pytest.raises(ConsistencyError):
#         event.mutate(resource)


# def test_release_created_has_id():
#     release = Release(
#         entity_id="e", name="e-name", publication_date=12345.0, description="ee"
#     )

#     assert release.id == "e"
#     assert release.name == "e-name"
#     assert release.publication_date == 12345.0
#     assert release.description == "ee"
#     assert release.root.id == release.id


# def test_release_created_w_resource_has_id():
#     resource = factories.ResourceFactory()
#     release = Release(
#         entity_id="e",
#         name="e-name",
#         publication_date=12345.0,
#         description="ee",
#         aggregate_root=resource,
#     )

#     assert release.id == "e"
#     assert release.name == "e-name"
#     assert release.publication_date == 12345.0
#     assert release.description == "ee"
#     assert release.root.id == resource.id


def test_resource_has_entry_json_schema():
    resource = factories.ResourceFactory()

    json_schema = resource.entry_json_schema

    assert json_schema["type"] == "object"
    assert "baseform" in json_schema["properties"]


@pytest.mark.parametrize(
    "field,value",
    [
        # ("resource_id", "new..1"),
        # ("config", {"b": "r"}),
        ("name", "New name"),
    ],
)
def test_discarded_resource_has_event(field, value):
    resource = random_resource()
    resource.discard(user="alice@example.org", message="bad", timestamp=123.45)
    assert resource.discarded
    assert resource.domain_events[-1] == events.ResourceDiscarded(
        entity_id=resource.id,
        # entry_repo_id=resource.entry_repository_id,
        resource_id=resource.resource_id,
        user=resource.last_modified_by,
        timestamp=resource.last_modified,
        message=resource.message,
        version=2,
        name=resource.name,
        config=resource.config,
    )
    with pytest.raises(errors.DiscardedEntityError):
        setattr(resource, field, value)


def test_published_resource_has_event():
    resource = random_resource()
    previous_version = resource.version
    resource.publish(
        user="kristoff@example.com", message="publish", version=resource.version
    )
    assert resource.is_published
    assert resource.version == (previous_version + 1)
    assert resource.domain_events[-1] == events.ResourcePublished(
        entity_id=resource.id,
        entry_repo_id=resource.entry_repository_id,
        resource_id=resource.resource_id,
        user=resource.last_modified_by,
        timestamp=resource.last_modified,
        version=resource.version,
        config=resource.config,
        name=resource.name,
        message=resource.message,
    )
