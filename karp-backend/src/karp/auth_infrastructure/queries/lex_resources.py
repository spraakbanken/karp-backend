import typing  # noqa: D100, I001

from karp.auth.application.queries.resources import ResourcePermissionDto
from karp.auth.domain import errors
from karp.foundation.value_objects.permission_level import PermissionLevel
from karp.lex_infrastructure import ResourceQueries


class LexGetResourcePermissions:
    def __init__(self, resources: ResourceQueries):
        self.resources = resources

    def query(self) -> typing.List[ResourcePermissionDto]:  # noqa: D102
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


class LexIsResourceProtected:
    def __init__(self, resource_queries: ResourceQueries) -> None:  # noqa: D107
        super().__init__()
        self.resource_queries = resource_queries

    def query(self, resource_id: str, level: PermissionLevel) -> bool:  # noqa: D102
        if level in [PermissionLevel.write, PermissionLevel.admin]:
            return True
        resource = self.resource_queries.by_resource_id_optional(resource_id=resource_id)
        if not resource:
            raise errors.ResourceNotFound(f"Can't find resource '{resource_id}'")
        return resource.config.get("protected", {}).get("read", False)
