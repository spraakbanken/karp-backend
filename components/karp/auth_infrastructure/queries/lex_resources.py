import typing

from karp.auth.domain import errors
from karp.auth.application.queries import (
    GetResourcePermissions,
    ResourcePermissionDto,
    IsResourceProtected,
)
from karp.foundation.value_objects.permission_level import PermissionLevel
from karp.lex.application.queries import (
    GetPublishedResources,
    ReadOnlyResourceRepository,
)


class LexGetResourcePermissions(GetResourcePermissions):
    def __init__(
        self,
        get_published_resources: GetPublishedResources,
    ):
        self.get_published_resources = get_published_resources

    def query(self) -> typing.List[ResourcePermissionDto]:
        resource_permissions = []
        for resource in self.get_published_resources.query():
            resource_obj = {"resource_id": resource.resource_id}

            protected_conf = resource.config.get("protected")
            if not protected_conf:
                protected = None
            elif protected_conf.get("admin"):
                protected = "ADMIN"
            elif protected_conf.get("write"):
                protected = "WRITE"
            else:
                protected = "READ"

            if protected:
                resource_obj["protected"] = protected
            resource_permissions.append(resource_obj)

        return resource_permissions


class LexIsResourceProtected(IsResourceProtected):
    def __init__(self, resource_repo: ReadOnlyResourceRepository) -> None:
        super().__init__()
        self.resource_repo = resource_repo

    def query(self, resource_id: str, level: PermissionLevel) -> bool:
        if level in [PermissionLevel.write, PermissionLevel.admin]:
            return True
        resource = self.resource_repo.get_by_resource_id(resource_id=resource_id)
        if not resource:
            raise errors.ResourceNotFound(f"Can't find resource '{resource_id}'")
        return resource.config.get("protected", {}).get("read", False)
