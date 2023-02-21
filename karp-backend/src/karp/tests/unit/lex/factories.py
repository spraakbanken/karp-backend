"""Factories used in tests."""
import typing  # noqa: I001

import factory
import factory.fuzzy
from faker.providers import BaseProvider

from karp.lex import commands
from karp.lex.domain import entities, events
from karp.foundation.value_objects import MachineName
from karp.lex_core.value_objects import make_unique_id
from karp.timings import utc_now


class ResourceConfigProvider(BaseProvider):
    def resource_config(self) -> typing.Dict:
        return {
            "sort": ["baseform"],
            "fields": {
                "baseform": {"type": "string", "required": True},
                "wordclass": {"type": "string"},
            },
            "id": "baseform",
        }


class MachineNameProvider(BaseProvider):
    def machine_name(self) -> MachineName:
        return MachineName(name=factory.fuzzy.FuzzyText(length=6, prefix="resource_"))


factory.Faker.add_provider(MachineNameProvider)
factory.Faker.add_provider(ResourceConfigProvider)


class ResourceFactory(factory.Factory):
    class Meta:
        model = entities.Resource

    id = factory.LazyFunction(make_unique_id)  # noqa: A003
    entry_repo_id = factory.LazyFunction(make_unique_id)
    resource_id: str = factory.Faker("word")
    name: str = factory.Faker("word")
    config: str = factory.Faker("resource_config")
    last_modified_by: str = factory.Faker("email")
    last_modified = factory.LazyFunction(utc_now)
    message = "resource created"


class EntryFactory(factory.Factory):
    class Meta:
        model = entities.Entry

    id = factory.LazyFunction(make_unique_id)  # noqa: A003
    # entry_id = factory.Faker("word")
    last_modified_by = factory.Faker("email")
    last_modified = factory.LazyFunction(utc_now)
    message = "entry created"
    body = {}
    repository_id = factory.LazyFunction(make_unique_id)


def random_resource(config: typing.Optional[typing.Dict] = None):  # noqa: ANN201
    config = config or {"fields": {"wf": {"type" "string"}, "id": "wf"}}
    return entities.create_resource(
        id=make_unique_id(),
        entry_repo_id=make_unique_id(),
        resource_id="resource",
        config=config,
        message="Resource add",
        created_by="kristoff@example.com",
    )


class ResourceCreatedFactory(factory.Factory):
    class Meta:
        model = events.ResourceCreated

    timestamp = factory.LazyFunction(utc_now)
    id = factory.LazyFunction(make_unique_id)  # noqa: A003
    entryRepoId = factory.LazyFunction(make_unique_id)
    resourceId = factory.Faker("word")
    name = factory.Faker("word")
    config = factory.Faker("resource_config")
    user = factory.Faker("email")
    message = "resource created"


class ResourcePublishedFactory(factory.Factory):
    class Meta:
        model = events.ResourcePublished

    timestamp = factory.LazyFunction(utc_now)
    id = factory.LazyFunction(make_unique_id)  # noqa: A003
    entryRepoId = factory.LazyFunction(make_unique_id)
    resourceId = factory.Faker("word")
    name = factory.Faker("word")
    config = factory.Faker("resource_config")
    user = factory.Faker("email")
    version = factory.Sequence(int)
    message = "resource created"


class EntryAddedFactory(factory.Factory):
    class Meta:
        model = events.EntryAdded

    timestamp = factory.LazyFunction(utc_now)
    id = factory.LazyFunction(make_unique_id)  # noqa: A003
    resource_id = factory.Faker("word")
    entry_id = factory.Faker("word")
    body = factory.Faker("resource_config")
    user = factory.Faker("email")
    message = "resource created"


class CreateEntryRepositoryFactory(factory.Factory):
    class Meta:
        model = commands.CreateEntryRepository

    # id = factory.LazyFunction(make_unique_id)
    name = factory.Faker("word")
    repositoryType = "fake"
    config = factory.Faker("resource_config")
    message = "entry repository created"
    user = factory.Faker("email")


class DeleteEntryRepositoryFactory(factory.Factory):
    class Meta:
        model = commands.DeleteEntryRepository

    id = factory.LazyFunction(make_unique_id)  # noqa: A003
    message = "entry repository deleted"
    user = factory.Faker("email")
    version = 2


class MachineNameFactory(factory.Factory):
    class Meta:
        model = MachineName

    name = factory.Faker("word")


class CreateResourceFactory(factory.Factory):
    class Meta:
        model = commands.CreateResource

    # id = factory.LazyFunction(make_unique_id)
    # resourceId = factory.SubFactory(MachineNameFactory)
    resourceId = factory.fuzzy.FuzzyText(length=6, prefix="resource_")
    name = factory.Faker("word")
    # repositoryType = "fake"
    config = factory.Faker("resource_config")
    entryRepoId = factory.LazyFunction(make_unique_id)
    message = "created"
    user = factory.Faker("email")


class UpdateResourceFactory(factory.Factory):
    class Meta:
        model = commands.UpdateResource

    resourceId = factory.Faker("word")
    name = factory.Faker("word")
    config = factory.Faker("resource_config")
    message = "created"
    user = "kristoff@example.com"


class AddEntryFactory(factory.Factory):
    class Meta:
        model = commands.AddEntry

    # id = factory.LazyFunction(make_unique_id)
    resourceId = factory.Faker("word")
    entry = {
        "baseform": "bra",
    }
    user = factory.Faker("email")
    message = "added"


class AddEntriesFactory(factory.Factory):
    class Meta:
        model = commands.AddEntries

    resourceId = factory.Faker("word")
    entries = [
        {
            "entry": {
                "baseform": "bra",
            }
        }
    ]
    user = factory.Faker("email")
    message = "added"


class AddEntriesInChunksFactory(AddEntriesFactory):
    class Meta:
        model = commands.AddEntriesInChunks

    chunkSize = 50


class ImportEntriesFactory(AddEntriesFactory):
    class Meta:
        model = commands.ImportEntries

    message = "imported"


class ImportEntriesInChunksFactory(AddEntriesInChunksFactory):
    class Meta:
        model = commands.ImportEntriesInChunks

    message = "imported"


class UpdateEntryFactory(factory.Factory):
    class Meta:
        model = commands.UpdateEntry

    resourceId = factory.Faker("word")
    entry = {}
    user = factory.Faker("email")
    message = "added"


class DeleteEntryFactory(factory.Factory):
    class Meta:
        model = commands.DeleteEntry

    resourceId = factory.Faker("word")
    user = factory.Faker("email")
    message = "deleted"
