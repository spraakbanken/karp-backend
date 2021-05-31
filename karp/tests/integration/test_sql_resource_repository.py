"""Tests for SQLResourceRepository"""
# from karp.cli import publish_resource
import uuid

import pytest

from karp.domain import model
from karp.domain.commands import CreateResource
from karp.domain.models.resource import ResourceOp, create_resource, Resource

from karp.domain.errors import IntegrityError

# from karp.domain.models.lexical_resource import LexicalResource
# from karp.infrastructure.unit_of_work import unit_of_work
from karp.services import handlers
from karp.infrastructure.sql import db
from karp.infrastructure.sql.sql_resource_repository import SqlResourceRepository
from karp.utility import unique_id, time

# pytestmark = pytest.mark.usefixtures("db_setup")


@pytest.fixture(name="resource_repo")  # , scope="module")
def fixture_resource_repo(sqlite_session_factory):
    session = sqlite_session_factory()
    return SqlResourceRepository(session)
    # return resource_repo


def test_sql_resource_repo_empty(resource_repo):
    assert resource_repo.resource_ids() == []
    assert resource_repo.history_by_resource_id("test_id") == []


def test_sql_resource_repo_put_resource(resource_repo):
    resource_id = "test_id"
    resource_name = "Test"
    resource_config = {
        "resource_id": resource_id,
        "resource_name": resource_name,
        "a": "b",
    }
    message = "add resource"
    # resource = create_resource(resource_config)
    id_ = unique_id.make_unique_id()
    resource = model.Resource(
        entity_id=id_,
        resource_id=resource_id,
        name=resource_name,
        config=resource_config,
        message=message,
    )

    resource_repo.put(resource)
    expected_version = 1

    assert resource_repo.resource_ids() == [resource_id]

    resource = resource_repo.by_id(id_)
    assert resource.version == expected_version
    assert resource.message == message
    assert resource.op == ResourceOp.ADDED

    resource_id_history = resource_repo.history_by_resource_id(resource_id)
    assert len(resource_id_history) == 1

    test_lex = resource_repo.by_resource_id(resource_id)

    assert isinstance(test_lex, Resource)
    assert isinstance(test_lex.config, dict)
    assert test_lex.resource_id == resource_id
    assert test_lex.id == resource.id
    assert test_lex.name == resource_name
    assert test_lex.version == expected_version


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
#         uw.put(resource)
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


# @pytest.mark.skip(reason="tested in unit tests")
def test_sql_resource_repo_putting_already_existing_resource_id_raises(resource_repo):
    resource_id = "test_id"
    resource_name = "Test"
    resource_config = {
        "resource_id": resource_id,
        "resource_name": resource_name,
        "a": "b",
    }
    message = "hhh"
    id_ = unique_id.make_unique_id()
    resource = model.Resource(
        entity_id=id_,
        resource_id=resource_id,
        name=resource_name,
        config=resource_config,
        message=message,
    )
    # cmd = CreateResource(
    #     id=id_,
    #     resource_id=resource_id,
    #     name=resource_name,
    #     config=resource_config,
    #     message=message,
    # )
    # # session = db.SessionLocal()
    # uow = unit_of_work(using=resource_repo)  # , session=session)

    # handlers.create_resource(cmd, uow)
    resource_repo.put(resource)

    assert len(resource_repo.resource_ids()) == 1
    res = resource_repo.by_resource_id(resource_id)

    assert res.id == id_

    # resource = create_resource(
    #     {"resource_id": resource_id, "resource_name": resource_name, "a": "b"}
    # )
    resource_2 = model.Resource(
        entity_id=uuid.uuid4(),
        resource_id=resource_id,
        name=resource_name,
        config=resource_config,
        message=message,
    )

    with pytest.raises(IntegrityError) as exc_info:
        resource_repo.put(resource_2)

    assert "Resource with resource_id 'test_id' already exists." in str(exc_info)


def test_sql_resource_repo_update_resource(resource_repo):
    resource_id = "test_id"
    resource_version = 1

    expected_config = {"a": "b"}
    resource_id = "test_id"
    resource_name = "Test"
    resource_config = {
        "a": "b",
    }
    id_ = uuid.uuid4()
    message = "hhh"
    resource = model.Resource(
        entity_id=id_,
        resource_id=resource_id,
        name=resource_name,
        config=resource_config,
        message=message,
    )
    resource_repo.put(resource)

    expected_version = 1

    assert resource_repo.resource_ids() == [resource_id]
    resource_copy_1 = resource_repo.by_id(id_)

    assert resource_copy_1.version == expected_version
    resource_id_history = resource_repo.history_by_resource_id(resource_id)
    assert len(resource_id_history) == 1

    resource.config = {"a": "changed", "c": "added"}
    resource.stamp(
        message="change config",
        user="Test user",
        timestamp=time.utc_now(),
    )
    # session = db.SessionLocal()
    resource_repo.update(resource)

    assert resource_repo.by_id(id_).version == 2
    assert resource_repo.by_resource_id(resource_id).version == 2

    assert resource_repo.resource_with_id_and_version(resource_id, 1).version == 1

    assert resource_repo.by_id(id_, version=1).version == 1
    assert resource_repo.by_resource_id(resource_id, version=1).version == 1

    resource_version += 1

    lex = resource_repo.by_resource_id(resource_id)

    assert lex is not None
    assert lex.resource_id == resource_id
    assert lex.version == resource_version
    assert resource_repo.get_latest_version(resource_id) == resource_version

    lex._version = 3
    resource_repo.put(lex)

    assert resource_repo.by_resource_id(resource_id).version == 3


def test_sql_resource_repo_2nd_active_raises(resource_repo):
    resource_id = "test_id"
    resource_version = 2
    with pytest.raises(Exception):
        with unit_of_work(using=resource_repo) as uw:
            resource = uw.resource_with_id_and_version(resource_id, resource_version)
            resource.is_published = True
            resource.stamp(user="Admin", message="make active")
            uw.update(resource)
            assert resource.is_published is True


def test_sql_resource_repo_version_change_to_existing_raises(resource_repo):
    resource_id = "test_id"
    resource_version = 2
    with pytest.raises(Exception):
        with unit_of_work(using=resource_repo) as uw:
            resource = uw.resource_with_id_and_version(resource_id, resource_version)
            resource.version = 1


def test_sql_resource_repo_put_another_resource(resource_repo):
    resource_id = "test_id"
    resource_name = "Test"
    resource_config = {
        "a": "b",
    }
    message = "hhh"
    resource = model.Resource(
        entity_id=unique_id.make_unique_id(),
        resource_id=resource_id,
        name=resource_name,
        config=resource_config,
        message=message,
    )
    resource_repo.put(resource)
    resource_id2 = "test_id_2"
    resource_config = {
        "fields": {"name": {"type": "string", "required": True}},
    }
    resource2 = model.Resource(
        entity_id=unique_id.make_unique_id(),
        resource_id=resource_id2,
        name=resource_name,
        config=resource_config,
        message=message,
    )
    resource_repo.put(resource2)

    assert resource_repo.resource_ids() == [resource_id, resource_id2]


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
#         uw.put(create_resource({"resource_id": "test_id_3", "resource_name": "g"}))
#         published_resources = uw.get_published_resources()

#         assert len(published_resources) == 1
#         assert published_resources[0].resource_id == "test_id_2"


# def test_sql_resource_repo_
