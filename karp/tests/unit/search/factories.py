import factory


from karp.search.domain import commands


class ReindexResourceFactory(factory.Factory):
    class Meta:
        model = commands.ReindexResource

    resource_id = factory.Faker("word")
