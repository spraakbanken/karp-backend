import factory

from karp.domain.model import Entry, Resource


class ResourceFactory(factory.Factory):
    class Meta:
        model = Resource

    # entity_id = factory.
