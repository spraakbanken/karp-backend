import typing

from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto
from karp.lex.application import repositories as lex_repositories


class LexGetResourcePermissions(GetResourcePermissions):
    def __init__(
        self,
        resource_uow: lex_repositories.ResourceUnitOfWork,
    ):
        self._resource_uow = resource_uow

    def query(self) -> typing.List[ResourcePermissionDto]:
        resource_permissions = []
        with self._resource_uow as uw:
            for resource in uw.repo.get_published_resources():
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
