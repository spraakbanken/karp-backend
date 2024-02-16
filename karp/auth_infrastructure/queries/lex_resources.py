import typing  # noqa: D100, I001

from karp.auth.application.queries.resources import ResourcePermissionDto
from karp.auth.domain import errors
from karp.auth.domain.entities.user import User
from karp.foundation.value_objects.permission_level import PermissionLevel
from karp.lex.application.repositories import ResourceRepository


class ResourcePermissionQueries:
    def __init__(self, resources: ResourceRepository):
        self.resources = resources

    def get_resource_permissions(self) -> typing.List[ResourcePermissionDto]:  # noqa: D102
        resource_permissions = []
        for resource in self.resources.get_published_resources():
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

    def is_resource_protected(self, resource_id: str, level: PermissionLevel) -> bool:  # noqa: D102
        if level in [PermissionLevel.write, PermissionLevel.admin]:
            return True
        resource = self.resources.by_resource_id_optional(resource_id=resource_id)
        if not resource:
            raise errors.ResourceNotFound(f"Can't find resource '{resource_id}'")
        return resource.config.get("protected", {}).get("read", False)

    def has_permission(  # noqa: ANN201, D102
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
