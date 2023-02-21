import factory  # noqa: I001


from karp.search.domain import commands


class ReindexResourceFactory(factory.Factory):
    class Meta:
        model = commands.ReindexResource

    resourceId = factory.Faker("word")
