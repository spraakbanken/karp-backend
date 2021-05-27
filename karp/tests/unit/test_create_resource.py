
from .adapters import FakeUnitOfWork, FakeResourceRepository
from karp.services import handlers
from karp.domain.commands import CreateResource
from karp.utility.unique_id import make_unique_id


def test_create_resource_creates_resource():
    id_ = make_unique_id()
    resource_id = "test_resource"
    resource_name = "Test resource"
    conf = {
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    message = "test_resource added"
#     with mock.patch("karp.utility.time.utc_now", return_value=12345):
#         resource = create_resource(conf)

    uow = FakeUnitOfWork(FakeResourceRepository())

    cmd = CreateResource(
        id=id_,
        resource_id=resource_id,
        name=resource_name,
        config=conf,
        message=message,
    )

    handlers.create_resource(cmd, uow)

    assert len(uow.repo) == 1

    assert uow.repo[0].id == id_
    assert uow.repo[0].resource_id == resource_id

    assert uow.repo[0].name == resource_name

    assert uow.repo[0].config == conf

    assert uow.was_committed

    assert uow.repo[0].events[-1] == events.ResourceCreated()

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



