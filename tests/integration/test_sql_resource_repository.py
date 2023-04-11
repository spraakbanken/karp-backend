"""Tests for SQLResourceRepository"""

import pytest  # noqa: I001

from karp.lex.domain.errors import IntegrityError  # noqa: F401
from karp.lex.domain.entities.resource import Resource, ResourceOp
from karp.lex_infrastructure.repositories.sql_resources import SqlResourceRepository
from tests.unit.lex import factories


@pytest.fixture(name="resource_repo")  # , scope="module")
def fixture_resource_repo(sqlite_session_factory):  # noqa: ANN201
    session = sqlite_session_factory()
    return SqlResourceRepository(session)


def test_sql_resource_repo_empty(resource_repo):  # noqa: ANN201
    assert resource_repo.resource_ids() == []


def test_sql_resource_repo_put_resource(resource_repo):  # noqa: ANN201
    resource = factories.ResourceFactory()

    resource_repo.save(resource)
    expected_version = 1  # noqa: F841

    assert resource_repo.resource_ids() == [resource.resource_id]

    resource_copy_1 = resource_repo.by_id(resource.id)
    assert resource_copy_1.version == resource.version
    assert resource_copy_1.message == resource.message
    assert resource_copy_1.op == ResourceOp.ADDED

    test_lex = resource_repo.by_resource_id(resource.resource_id)

    assert isinstance(test_lex, Resource)
    assert isinstance(test_lex.config, dict)
    assert test_lex.resource_id == resource.resource_id
    assert test_lex.id == resource.id
    assert test_lex.name == resource.name
    assert test_lex.version == resource.version


def test_sql_resource_repo_update_resource(resource_repo):  # noqa: ANN201
    resource = factories.ResourceFactory(
        config={"a": "b"},
    )
    resource_repo.save(resource)

    resource.set_config(
        config={"a": "changed", "c": "added"},
        message="change config",
        user="Test user",
        version=1,
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

    lex.set_config(
        config={"a": "changed", "c": "added", "d": "added"},
        user="kristoff@example.com",
        version=lex.version,
        # message='update'
    )
    assert lex.version == 3
    resource_repo.save(lex)

    assert resource_repo.get_by_resource_id(resource.resource_id).version == 3


def test_sql_resource_repo_put_another_resource(resource_repo):  # noqa: ANN201
    resource = factories.ResourceFactory()
    resource_repo.save(resource)

    resource2 = factories.ResourceFactory()
    resource_repo.save(resource2)

    assert set(resource_repo.resource_ids()) == set(  # noqa: C405
        [resource.resource_id, resource2.resource_id]
    )


class TestSqlResourceRepo:
    def test_discard_resource_and_insert_new(self, resource_repo):  # noqa: ANN201
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

    def test_change_resource_id_changes_resource_ids(  # noqa: ANN201
        self, resource_repo
    ):
        resource = factories.ResourceFactory()
        resource_repo.save(resource)

        resource.set_resource_id(
            resource_id="changed_id",
            user="kristoff@example.com",
            version=1,
        )
        resource_repo.save(resource)

        assert resource_repo.resource_ids() == ["changed_id"]
