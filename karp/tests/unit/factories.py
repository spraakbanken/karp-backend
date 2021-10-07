"""Factories used in tests."""
import typing

import factory
from faker import Faker
from faker.providers import BaseProvider

from karp.lex.domain import events as lex_events
from karp.lex.domain import value_objects
from karp.lex.domain.value_objects import factories as lex_factories
from karp.domain import model
from karp.domain.models import resource
from karp.utility.time import utc_now


class ResourceConfigProvider(BaseProvider):
    def resource_config(self) -> typing.Dict:
        return {'fields': {}, 'id': 'id'}


factory.Faker.add_provider(ResourceConfigProvider)


class ResourceFactory(factory.Factory):
    class Meta:
        model = resource.Resource

    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker("word")
    last_modified_by = factory.Faker("email")
    last_modified = factory.LazyFunction(utc_now)


def random_resource(config: typing.Optional[typing.Dict] = None):
    config = config or {"fields": {"wf": {"type" "string"}, "id": "wf"}}
    return model.create_resource(
        entity_id=lex_factories.make_unique_id(),
        resource_id="resource",
        config=config,
        message="Resource add",
        created_by="kristoff@example.com",
    )


class ResourceCreatedFactory(factory.Factory):
    class Meta:
        model = lex_events.ResourceCreated

    timestamp = factory.LazyFunction(utc_now)
    id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    name = factory.Faker('word')
    config = factory.Faker('resource_config')
    user = factory.Faker('email')
    message = 'resource created'
