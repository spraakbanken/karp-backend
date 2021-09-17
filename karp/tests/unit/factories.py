from karp.domain.value_objects.unique_id import make_unique_id
import typing
import factory

from karp.domain.models import resource
from karp.domain import value_objects


class ResourceFactory(factory.Factory):
    class Meta:
        model = resource.Resource

    entity_id = factory.LazyFunction(value_objects.make_unique_id)
    resource_id = factory.Faker("word")
    last_modified_by = factory.Faker("email")
    last_modified = factory.LazyFunction()


def random_resource(config: typing.Optional[typing.Dict] = None):
    config = config or {"fields": {"wf": {"type" "string"}, "id": "wf"}}
    return model.create_resource(
        entity_id=value_objects.make_unique_id(),
        resource_id="resource",
        config=config,
        message="Resource add",
        created_by="kristoff@example.com",
    )
