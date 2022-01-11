from karp.application import schemas
from karp.domain.errors import RepositoryStatusError
from karp.services import context


def check_database_status(ctx: context.Context) -> schemas.SystemResponse:
    print(f"context = {context!r}")
    if ctx.resource_uow is None:
        return schemas.SystemNotOk(message="No resource_repository is configured.")
    try:
        # to check database we will execute raw query
        with ctx.resource_uow as uw:
            uw.repo.check_status()
    except RepositoryStatusError as e:
        return schemas.SystemNotOk(message=str(e))

    return schemas.SystemOk()
