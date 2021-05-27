
from .adapters import FakeUnitOfWork
from karp.services import CreateResourceHandler
from karp.domain.commands import CreateResourceCommand
from karp.utility.unique_id import make_unique_id


def test_create_resource_creates_resource():
    resource_id = make_unique_id()
    short_name = "test_resource"
    resource_name = "Test resource"
    conf = {
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    message = "test_resource added"
#     with mock.patch("karp.utility.time.utc_now", return_value=12345):
#         resource = create_resource(conf)

    uow = FakeUnitOfWork()

    handler = CreateResourceHandler(uow)
    cmd = CreateResourceCommand(
        resource_id=resource_id,
        short_name=short_name,
        name=resource_name,
        config=conf,
        message=message,
    )

    handler.handle(cmd)

    assert len(uow.resources) == 1

    assert uow.resources[0].id == resource_id

    assert uow.resources[0].name == resource_name
    assert uow.resources[0].short_name == short_name

    assert uow.resources[0].config == conf

    assert uow.was_committed

    # assert isinstance(resource, Resource)
    # assert resource.id == uuid.UUID(str(resource.id), version=4)
    # assert resource.version == 1
    # assert resource.resource_id == resource_id
    # assert resource.name == name
    # assert not resource.discarded
    # assert not resource.is_published
    # assert "resource_id" not in resource.config
    # assert "resource_name" not in resource.config
    # assert "sort" in resource.config
    # assert resource.config["sort"] == conf["sort"]
    # assert "fields" in resource.config
    # assert resource.config["fields"] == conf["fields"]
    # assert int(resource.last_modified) == 12345
    # assert resource.message == "Resource added."
    # assert resource.op == ResourceOp.ADDED



