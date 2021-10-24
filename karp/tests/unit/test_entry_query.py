import pytest

# from karp.search.domain import errors, index
# from karp.services import entry_query
# from karp.tests import random_refs

# from .adapters import bootstrap_test_app

pytestmark = pytest.mark.skip()


class TestSearchIds:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            entry_query.search_ids("non_existing", "entry", bus.ctx)

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()
        bus.handle(random_refs.make_create_resource_command("existing"))
        with pytest.raises(errors.ResourceNotPublished):
            entry_query.search_ids("existing", "entry", bus.ctx)


class TestQuery:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            query_request = index.QueryRequest(resource_ids="non_existing")
            entry_query.query(query_request, bus.ctx)

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()
        bus.handle(random_refs.make_create_resource_command("existing"))
        with pytest.raises(errors.ResourceNotPublished):
            query_request = index.QueryRequest(resource_ids="existing")
            entry_query.query(query_request, bus.ctx)


class TestQuerySplit:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()
        with pytest.raises(errors.ResourceNotFound):
            query_request = index.QueryRequest(resource_ids="non_existing")
            entry_query.query_split(query_request, bus.ctx)

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()
        bus.handle(random_refs.make_create_resource_command("existing"))
        with pytest.raises(errors.ResourceNotPublished):
            query_request = index.QueryRequest(resource_ids="existing")
            entry_query.query_split(query_request, bus.ctx)
