

from karp.search_infrastructure.repositories.es6_indicies import Es6Index, Es6IndexUnitOfWork


class TestEs6Index:
    def test_can_instantiate_es6_index(self):
        try:
            Es6Index(None)
        except AttributeError:
            pass

    def test_can_instantiate_es6_index_uow(self):
        try:
            Es6IndexUnitOfWork(None, event_bus=None)
        except AttributeError:
            pass
