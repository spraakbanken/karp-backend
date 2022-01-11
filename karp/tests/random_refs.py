import typing

from karp.domain import commands
from karp.domain.value_objects.unique_id import make_unique_id


def make_create_resource_command(
    resource_id: str, config: typing.Optional[typing.Dict] = None
) -> commands.CreateResource:
    config = config or {
        "fields": {},
        "id": "id",
    }
    return commands.CreateResource(
        id=make_unique_id(),
        resource_id=resource_id,
        name=resource_id.upper(),
        config=config,
        message="create resource",
        created_by="kristoff@example.com",
    )
