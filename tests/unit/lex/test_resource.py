import copy  # noqa: I001
from unittest import mock

import pytest

from karp.lex.domain import errors, events
from karp.lex.domain.entities.resource import (
    Resource,
    ResourceOp,
    create_resource,
)
from karp.lex_core.value_objects import make_unique_id, unique_id

from . import factories
from .factories import random_resource


def test_create_resource_creates_resource():  # noqa: ANN201
    resource_id = "test_resource"
    name = "Test resource"
    conf = {
        "resource_id": resource_id,
        "resource_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    with mock.patch("karp.timings.utc_now", return_value=12345):
        resource, domain_events = create_resource(
            conf,
            created_by="kristoff@example.com",
            entry_repo_id=unique_id.make_unique_id(),
        )

    assert isinstance(resource, Resource)
    assert isinstance(resource.entity_id, unique_id.UniqueIdType)
    assert resource.id == unique_id.parse(str(resource.id))
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
    assert domain_events[-1] == events.ResourceCreated(
        timestamp=resource.last_modified,
        id=resource.id,
        entryRepoId=resource.entry_repository_id,
        resourceId=resource.resource_id,
        name=resource.name,
        config=resource.config,
        user=resource.last_modified_by,
        message=resource.message,
    )


def test_resource_update_changes_last_modified_and_version():  # noqa: ANN201
    resource_id = "test_resource"
    name = "Test resource"
    conf = {
        "resource_id": resource_id,
        "resource_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }

    resource = factories.ResourceFactory(name=copy.deepcopy(name), config=copy.deepcopy(conf))
    previous_last_modified = resource.last_modified
    previous_version = resource.version

    conf["fields"]["new"] = {"type": "string"}
    domain_events = resource.update(name="new name", config=conf, user="Test", version=1)

    assert resource.last_modified > previous_last_modified
    assert resource.last_modified_by == "Test"
    assert resource.version == (previous_version + 1)
    assert domain_events[-1] == events.ResourceUpdated(
        timestamp=resource.last_modified,
        id=resource.id,
        entryRepoId=resource.entry_repository_id,
        resourceId=resource.resource_id,
        name=resource.name,
        config=resource.config,
        user=resource.last_modified_by,
        message=resource.message,
        version=resource.version,
    )


def test_resource_has_entry_json_schema():  # noqa: ANN201
    resource = factories.ResourceFactory.build()

    json_schema = resource.entry_schema

    assert json_schema is not None


class TestDiscardedResource:
    def test_discarded_resource_has_event(self) -> None:
        resource, _ = random_resource()
        domain_events = resource.discard(
            user="alice@example.org", message="bad", timestamp=12345678.9
        )
        assert resource.discarded
        assert domain_events[-1] == events.ResourceDiscarded(
            id=resource.id,
            resourceId=resource.resource_id,
            user=resource.last_modified_by,
            timestamp=resource.last_modified,
            message=resource.message,
            version=2,
            name=resource.name,
            config=resource.config,
        )

    def test_discarded_resource_cant_be_updated(self) -> None:
        resource, _ = random_resource()
        _domain_events = resource.discard(user="alice@example.org", message="bad")
        with pytest.raises(errors.DiscardedEntityError):
            resource.publish(user="user1", message="publish", version=1)
        with pytest.raises(errors.DiscardedEntityError):
            resource.set_entry_repo_id(
                entry_repo_id=make_unique_id(),
                user="user1",
                message="publish",
                version=1,
            )
        with pytest.raises(errors.DiscardedEntityError):
            resource.set_resource_id(
                resource_id="new",
                user="user1",
                message="publish",
                version=1,
            )
        with pytest.raises(errors.DiscardedEntityError):
            resource.update(
                name="new",
                config=resource.config,
                user="user1",
                message="publish",
                version=1,
            )


def test_published_resource_has_event():  # noqa: ANN201
    resource, _ = random_resource()
    previous_version = resource.version
    domain_events = resource.publish(
        user="kristoff@example.com", message="publish", version=resource.version
    )
    assert resource.is_published
    assert resource.version == (previous_version + 1)
    assert domain_events[-1] == events.ResourcePublished(
        id=resource.id,
        entryRepoId=resource.entry_repository_id,
        resourceId=resource.resource_id,
        user=resource.last_modified_by,
        timestamp=resource.last_modified,
        version=resource.version,
        config=resource.config,
        name=resource.name,
        message=resource.message,
    )


class TestUpdateResource:
    def test_update_without_changes_returns_empty_list(self) -> None:
        resource, _ = random_resource()
        domain_events = resource.update(
            name=resource.name,
            config=resource.config,
            user=resource.last_modified_by,
            version=resource.version,
        )

        assert not domain_events


class TestResourceSetEntryRepoId:
    def test_set_entry_repo_id_returns_event(self) -> None:
        resource, _ = random_resource()
        entry_repo_id = make_unique_id()
        username = "user1"
        domain_events = resource.set_entry_repo_id(
            entry_repo_id=entry_repo_id,
            user=username,
            version=resource.version,
        )

        assert domain_events[0].entry_repo_id == entry_repo_id
        assert domain_events[0].user == username


class TestResourceSetResourceId:
    def test_set_resource_id_returns_event(self) -> None:
        resource, _ = random_resource()
        resource_id = "plus"
        username = "user1"
        domain_events = resource.set_resource_id(
            resource_id=resource_id,
            user=username,
            version=resource.version,
        )

        assert domain_events[0].resource_id == resource_id
        assert domain_events[0].user == username


class TestResourceSetConfig:
    def test_set_config_without_changes_returns_empty_list(self) -> None:
        resource, _ = random_resource()
        domain_events = resource.set_config(
            config=resource.config,
            user=resource.last_modified_by,
            version=resource.version,
        )

        assert not domain_events

    def test_set_config_returns_event(self) -> None:
        resource, _ = random_resource()
        config = {"fields": {"ff": {"type": "string"}}}
        username = "user1"
        domain_events = resource.set_config(
            config=config,
            user=username,
            version=resource.version,
        )

        assert domain_events[0].config == config
        assert domain_events[0].user == username
