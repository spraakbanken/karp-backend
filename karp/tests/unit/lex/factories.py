"""Factories used in tests."""
import typing

import factory
from faker import Faker
from faker.providers import BaseProvider

from karp.lex.domain import events as lex_events, commands as lex_commands, entities as lex_entities
from karp.foundation.value_objects import factories as lex_factories
from karp.utility.time import utc_now


class ResourceConfigProvider(BaseProvider):
    def resource_config(self) -> typing.Dict:
        return {
            "sort": ["baseform"],
            "fields": {
                "baseform": {"type": "string", "required": True},
                'wordclass': {'type': 'string'},
            },
            "id": "baseform",
        }


factory.Faker.add_provider(ResourceConfigProvider)


class ResourceFactory(factory.Factory):
    class Meta:
        model = lex_entities.Resource

    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    entry_repo_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker("word")
    name = factory.Faker('word')
    config = factory.Faker('resource_config')
    last_modified_by = factory.Faker("email")
    last_modified = factory.LazyFunction(utc_now)
    message = 'resource created'


class EntryFactory(factory.Factory):
    class Meta:
        model = lex_entities.Entry

    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    entry_id = factory.Faker("word")
    last_modified_by = factory.Faker("email")
    last_modified = factory.LazyFunction(utc_now)
    message = 'entry created'
    body = {}
    repository_id = factory.LazyFunction(lex_factories.make_unique_id)


def random_resource(config: typing.Optional[typing.Dict] = None):
    config = config or {"fields": {"wf": {"type" "string"}, "id": "wf"}}
    return lex_entities.create_resource(
        entity_id=lex_factories.make_unique_id(),
        entry_repo_id=lex_factories.make_unique_id(),
        resource_id="resource",
        config=config,
        message="Resource add",
        created_by="kristoff@example.com",
    )


class ResourceCreatedFactory(factory.Factory):
    class Meta:
        model = lex_events.ResourceCreated

    timestamp = factory.LazyFunction(utc_now)
    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    entry_repo_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    name = factory.Faker('word')
    config = factory.Faker('resource_config')
    user = factory.Faker('email')
    message = 'resource created'


class ResourcePublishedFactory(factory.Factory):
    class Meta:
        model = lex_events.ResourcePublished

    timestamp = factory.LazyFunction(utc_now)
    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    entry_repo_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    name = factory.Faker('word')
    config = factory.Faker('resource_config')
    user = factory.Faker('email')
    version = factory.Sequence(int)
    message = 'resource created'


class EntryAddedFactory(factory.Factory):
    class Meta:
        model = lex_events.EntryAdded

    timestamp = factory.LazyFunction(utc_now)
    id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    entry_id = factory.Faker('word')
    body = factory.Faker('resource_config')
    user = factory.Faker('email')
    message = 'resource created'


class CreateEntryRepositoryFactory(factory.Factory):
    class Meta:
        model = lex_commands.CreateEntryRepository

    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    name = factory.Faker('word')
    repository_type = 'fake'
    config = factory.Faker('resource_config')
    message = 'entry repository created'
    user = factory.Faker('email')


class CreateResourceFactory(factory.Factory):
    class Meta:
        model = lex_commands.CreateResource

    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    name = factory.Faker('word')
    repository_type = 'fake'
    config = factory.Faker('resource_config')
    entry_repo_id = factory.LazyFunction(lex_factories.make_unique_id)
    message = 'created'
    created_by = 'kristoff@example.com'


class UpdateResourceFactory(factory.Factory):
    class Meta:
        model = lex_commands.UpdateResource

    # entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    name = factory.Faker('word')
    repository_type = 'fake'
    config = factory.Faker('resource_config')
    entry_repo_id = factory.LazyFunction(lex_factories.make_unique_id)
    message = 'created'
    created_by = 'kristoff@example.com'


class AddEntryFactory(factory.Factory):
    class Meta:
        model = lex_commands.AddEntry

    entity_id = factory.LazyFunction(lex_factories.make_unique_id)
    resource_id = factory.Faker('word')
    entry = {
        'baseform': 'bra',
    }
    user = factory.Faker('email')
    message = 'added'


class UpdateEntryFactory(factory.Factory):
    class Meta:
        model = lex_commands.UpdateEntry

    resource_id = factory.Faker('word')
    entry_id = factory.Faker('word')
    entry = {}
    user = factory.Faker('email')
    message = 'added'


class DeleteEntryFactory(factory.Factory):
    class Meta:
        model = lex_commands.DeleteEntry

    resource_id = factory.Faker('word')
    entry_id = factory.Faker('word')
    user = factory.Faker('email')
    message = 'deleted'
