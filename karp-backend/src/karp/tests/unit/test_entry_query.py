import pytest

# from karp.search.domain import errors, index
# from karp.services import entry_query
# from karp.tests import random_refs

# from .adapters import bootstrap_test_app

pytestmark = pytest.mark.skip()


class TestSearchIds:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()  # noqa: F821
        with pytest.raises(errors.ResourceNotFound):  # noqa: F821
            entry_query.search_ids("non_existing", "entry", bus.ctx)  # noqa: F821

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()  # noqa: F821
        bus.handle(random_refs.make_create_resource_command("existing"))  # noqa: F821
        with pytest.raises(errors.ResourceNotPublished):  # noqa: F821
            entry_query.search_ids("existing", "entry", bus.ctx)  # noqa: F821


class TestQuery:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()  # noqa: F821
        with pytest.raises(errors.ResourceNotFound):  # noqa: F821
            query_request = index.QueryRequest(  # noqa: F821
                resource_ids="non_existing"
            )  # noqa: F821
            entry_query.query(query_request, bus.ctx)  # noqa: F821

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()  # noqa: F821
        bus.handle(random_refs.make_create_resource_command("existing"))  # noqa: F821
        with pytest.raises(errors.ResourceNotPublished):  # noqa: F821
            query_request = index.QueryRequest(resource_ids="existing")  # noqa: F821
            entry_query.query(query_request, bus.ctx)  # noqa: F821


class TestQuerySplit:
    def test_cannot_search_non_existent_resource(self):
        bus = bootstrap_test_app()  # noqa: F821
        with pytest.raises(errors.ResourceNotFound):  # noqa: F821
            query_request = index.QueryRequest(  # noqa: F821
                resource_ids="non_existing"
            )  # noqa: F821
            entry_query.query_split(query_request, bus.ctx)  # noqa: F821

    def test_cannot_search_non_published_resource(self):
        bus = bootstrap_test_app()  # noqa: F821
        bus.handle(random_refs.make_create_resource_command("existing"))  # noqa: F821
        with pytest.raises(errors.ResourceNotPublished):  # noqa: F821
            query_request = index.QueryRequest(resource_ids="existing")  # noqa: F821
            entry_query.query_split(query_request, bus.ctx)  # noqa: F821
