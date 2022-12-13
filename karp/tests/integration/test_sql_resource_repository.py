"""Tests for SQLResourceRepository"""

import pytest

from karp.lex.domain.errors import IntegrityError
from karp.lex.domain.entities.resource import Resource, ResourceOp
from karp.lex_infrastructure.repositories.sql_resources import SqlResourceRepository
from karp.tests.unit.lex import factories


@pytest.fixture(name="resource_repo")  # , scope="module")
def fixture_resource_repo(sqlite_session_factory):
    session = sqlite_session_factory()
    return SqlResourceRepository(session)


def test_sql_resource_repo_empty(resource_repo):
    assert resource_repo.resource_ids() == []
    assert resource_repo.history_by_resource_id("test_id") == []


def test_sql_resource_repo_put_resource(resource_repo):
    resource = factories.ResourceFactory()

    resource_repo.save(resource)
    expected_version = 1

    assert resource_repo.resource_ids() == [resource.resource_id]

    resource_copy_1 = resource_repo.by_id(resource.id)
    assert resource_copy_1.version == resource.version
    assert resource_copy_1.message == resource.message
    assert resource_copy_1.op == ResourceOp.ADDED

    resource_id_history = resource_repo.history_by_resource_id(resource.resource_id)
    assert len(resource_id_history) == 1

    test_lex = resource_repo.by_resource_id(resource.resource_id)

    assert isinstance(test_lex, Resource)
    assert isinstance(test_lex.config, dict)
    assert test_lex.resource_id == resource.resource_id
    assert test_lex.id == resource.id
    assert test_lex.name == resource.name
    assert test_lex.version == resource.version


#     # Update resource
#     with unit_of_work(using=resource_repo) as uw:
#         resource.config["c"] = "added"
#         resource.config["a"] = "changed"
#         resource.is_published = True
#         resource.stamp(user="Test user", message="change config")
#         uw.update(resource)
#         assert resource.version == 2
#
#     with unit_of_work(using=resource_repo) as uw:
#         test_lex = uw.by_resource_id(resource_id)
#
#         assert test_lex is not None
#         assert test_lex.config["a"] == "changed"
#         assert test_lex.config["c"] == "added"
#         assert test_lex.is_published is True
#         assert test_lex.version == 2
#         assert uw.get_latest_version(resource_id) == test_lex.version
#
#     # Test history
#     with unit_of_work(using=resource_repo) as uw:
#         resource_id_history = uw.history_by_resource_id(resource_id)
#
#         assert len(resource_id_history) == 2
#         assert resource_id_history[0].version == 2
#         assert resource_id_history[1].version == 1


# def test_sql_resource_repo_put_lexical_resource(resource_repo):
#     resource_id = "test_id"
#     resource_name = "Test"
#     resource_config = {
#         "resource_id": resource_id,
#         "resource_name": resource_name,
#         "a": "b",
#     }
#     resource = Resource.create_resource("lexical_resource", resource_config)

#     expected_version = 1

#     with unit_of_work(using=resource_repo) as uw:
#         uw.save(resource)
#         uw.commit()
#         assert uw.resource_ids() == [resource_id]

#         assert resource.version == expected_version
#         assert resource.message == "Resource added."
#         assert resource.op == ResourceOp.ADDED
#         resource_id_history = uw.history_by_resource_id(resource_id)
#         assert len(resource_id_history) == 1

#     with unit_of_work(using=resource_repo) as uw:
#         test_lex = uw.resource_with_id_and_version(resource_id, expected_version)

#         assert isinstance(test_lex, Resource)
#         assert isinstance(test_lex, LexicalResource)
#         assert isinstance(test_lex.config, dict)
#         assert test_lex.resource_id == resource_id
#         assert test_lex.id == resource.id
#         assert test_lex.name == resource_name


#     {"resource_id": resource_id, "resource_name": resource_name, "a": "b"}
# )


def test_sql_resource_repo_update_resource(resource_repo):
    resource = factories.ResourceFactory(
        config={"a": "b"},
    )
    resource_repo.save(resource)

    resource.set_config(
        config={"a": "changed", "c": "added"},
        message="change config",
        user="Test user",
        version=1,
        # timestamp=time.utc_now(),
    )
    resource_repo.save(resource)

    assert resource_repo.by_id(resource.id).version == 2
    assert resource_repo.by_resource_id(resource.resource_id).version == 2

    assert resource_repo.get_by_id(resource.entity_id, version=1).version == 1
    assert (
        resource_repo.get_by_resource_id(resource.resource_id, version=1).version == 1
    )

    lex = resource_repo.by_resource_id(resource.resource_id)
    assert lex is not None
    assert lex.resource_id == resource.resource_id
    assert resource_repo.get_latest_version(resource.resource_id) == resource.version

    lex.set_config(
        config={"a": "changed", "c": "added", "d": "added"},
        user="kristoff@example.com",
        version=lex.version,
        # message='update'
    )
    assert lex.version == 3
    resource_repo.save(lex)

    assert resource_repo.get_by_resource_id(resource.resource_id).version == 3


def test_sql_resource_repo_put_another_resource(resource_repo):
    resource = factories.ResourceFactory()
    resource_repo.save(resource)

    resource2 = factories.ResourceFactory()
    resource_repo.save(resource2)

    assert resource_repo.resource_ids() == [resource.resource_id, resource2.resource_id]


class TestSqlResourceRepo:
    def test_discard_resource_and_insert_new(self, resource_repo):
        resource = factories.ResourceFactory()
        resource_repo.save(resource)

        resource.discard(
            user="kristoff@example.com",
            message="delete",
        )
        resource_repo.save(resource)

        resource2 = factories.ResourceFactory(
            resource_id=resource.resource_id,
        )
        resource_repo.save(resource2)

        assert resource_repo.get_by_resource_id(resource.resource_id).version == 1

        assert resource_repo.resource_ids() == [resource.resource_id]

    def test_change_resource_id_changes_resource_ids(self, resource_repo):
        resource = factories.ResourceFactory()
        resource_repo.save(resource)

        resource.set_resource_id(
            resource_id="changed_id",
            user="kristoff@example.com",
            version=1,
        )
        resource_repo.save(resource)

        assert resource_repo.resource_ids() == ["changed_id"]


# def test_sql_resource_repo_deep_update_of_resource(resource_repo):
#     with unit_of_work(using=resource_repo) as uw:
#         resource = uw.get_active_resource("test_id_2")
#         assert resource is not None

#         resource.config["fields"]["count"] = {"type": "int"}
#         resource.stamp(user="Admin", message="change")
#         assert resource.is_published
#         assert resource.version == 2
#         uw.update(resource)
#         # assert resource.name_id == "test_id_2Test 2"

#     with unit_of_work(using=resource_repo) as uw:
#         resource = uw.get_active_resource("test_id_2")

#         assert resource is not None
#         assert "count" in resource.config["fields"]
#         assert resource.config["fields"]["count"] == {"type": "int"}


# def test_get_published_resources(resource_repo):
#     with unit_of_work(using=resource_repo) as uw:
#         uw.save(create_resource({"resource_id": "test_id_3", "resource_name": "g"}))
#         published_resources = uw.get_published_resources()

#         assert len(published_resources) == 1
#         assert published_resources[0].resource_id == "test_id_2"


# def test_sql_resource_repo_
