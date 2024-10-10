import typing

from karp.auth.application.resources import ResourcePermissionDto
from karp.auth.domain import errors
from karp.auth.domain.user import User
from karp.foundation.value_objects.permission_level import PermissionLevel
from karp.lex.infrastructure import ResourceRepository


class ResourcePermissionQueries:
    def __init__(self, resources: ResourceRepository):
        self.resources = resources

    def get_resource_permissions(self) -> typing.List[ResourcePermissionDto]:
        resource_permissions = []
        for resource in self.resources.get_published_resources():
            protected_conf = resource.config.protected
            if not protected_conf:
                protected = None
            elif protected_conf.get("admin"):
                protected = "ADMIN"
            elif protected_conf.get("write"):
                protected = "WRITE"
            else:
                protected = "READ"
            resource_permissions.append(ResourcePermissionDto(resource_id=resource.resource_id, protected=protected))

        return resource_permissions

    def is_resource_protected(self, resource_id: str, level: PermissionLevel) -> bool:
        if level in [PermissionLevel.write, PermissionLevel.admin]:
            return True
        resource = self.resources.by_resource_id(resource_id=resource_id)
        return resource.config.protected.get("read", False)

    def has_permission(
        self,
        level: PermissionLevel,
        user: User,
        resource_ids: typing.List[str],
    ) -> bool:
        return not any(
            self.is_resource_protected(resource_id, level)
            and (not user or not user.has_enough_permissions(resource_id, level))
            for resource_id in resource_ids
        )
