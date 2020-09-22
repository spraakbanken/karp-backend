from karp.application import schemas
from karp.application.context import Context
from karp.domain.errors import RepositoryStatusError
from karp.infrastructure.unit_of_work import unit_of_work


def check_database_status(context: Context) -> schemas.SystemResponse:
    print(f"context = {context!r}")
    if context.resource_repo is None:
        return schemas.SystemNotOk(message="No resource_repository is configured.")
    try:
        # to check database we will execute raw query
        with unit_of_work(using=context.resource_repo) as uw:
            uw.check_status()
    except RepositoryStatusError as e:
        return schemas.SystemNotOk(message=str(e))

    return schemas.SystemOk()
