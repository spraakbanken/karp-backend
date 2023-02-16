import factory  # noqa: I001

from karp.domain.model import Entry, Resource  # noqa: F401


class ResourceFactory(factory.Factory):
    class Meta:
        model = Resource

    # entity_id = factory.
