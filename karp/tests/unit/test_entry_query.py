import pytest

from karp.domain import index, errors
from karp.services import entry_query

from karp.tests import random_refs
from .adapters import bootstrap_test_app


class TestSearchIds:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            entry_query.search_ids("non_existing", ["entry"], bus.ctx)

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()
        bus.handle(
            random_refs.make_create_resource_command("existing"))
        with pytest.raises(errors.ResourceNotPublished):
            entry_query.search_ids("existing", ["entry"], bus.ctx)


class TestQuery:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            entry_query.query("non_existing", ["entry"], bus.ctx)

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()
        bus.handle(
            random_refs.make_create_resource_command("existing"))
        with pytest.raises(errors.ResourceNotPublished):
            entry_query.query("existing", ["entry"], bus.ctx)


class TestQuerySplit:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            entry_query.query_split("non_existing", ["entry"], bus.ctx)

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()
        bus.handle(
            random_refs.make_create_resource_command("existing"))
        with pytest.raises(errors.ResourceNotPublished):
            entry_query.query_split("existing", ["entry"], bus.ctx)
