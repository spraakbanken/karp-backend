import typing
from karp.domain import errors, index, repository
from karp.services import context


def repo_check_resource_is_published(
    resource_id: str, repo: repository.ResourceRepository
):
    resource = repo.by_resource_id(resource_id)
    if not resource:
        raise errors.ResourceNotFound(resource_id)
    if not resource.is_published:
        raise errors.ResourceNotPublished(resource_id)


def check_resource_published(resource_id: str, ctx: context.Context):
    with ctx.resource_uow:
        resource = ctx.resource_uow.repo.by_resource_id(resource_id)
        if not resource:
            raise errors.ResourceNotFound(resource_id)
        if not resource.is_published:
            raise errors.ResourceNotPublished(resource_id)


def check_all_resources_published(
    resource_ids: typing.Iterable[str], ctx: context.Context
):
    with ctx.resource_uow:
        for resource_id in resource_ids:
            repo_check_resource_is_published(resource_id, ctx.resource_uow.repo)


def search_ids(resource_id: str, entry_ids: str, ctx: context.Context):
    check_resource_published(resource_id, ctx)
    with ctx.index_uow:
        return ctx.index_uow.repo.search_ids(resource_id, entry_ids)


def query(req: index.QueryRequest, ctx: context.Context):
    print(f"entry_query.query called with req={req}")
    check_all_resources_published(req.resource_ids, ctx)

    with ctx.index_uow:
        return ctx.index_uow.repo.query(req)
    # resources_service.check_resource_published(resource_list)

    # args = {
    #     "from": from_,
    #     "q": q,
    #     "size": size,
    #     "lexicon_stats": str(lexicon_stats),
    # }
    # search_query = bus.ctx.search_service.build_query(args, resources)
    # print(f"webapp.views.query.query:search_query={search_query}")
    # response = bus.ctx.search_service.search_with_query(search_query)


def query_split(req: index.QueryRequest, ctx: context.Context):
    check_all_resources_published(req.resource_ids, ctx)
    with ctx.index_uow as uw:
        return uw.repo.query_split(req)
    # resources_service.check_resource_published(resource_list)

    # args = {
    #     "from": from_,
    #     "q": q,
    #     "size": size,
    #     "lexicon_stats": str(lexicon_stats),
    # }
    # search_query = bus.ctx.search_service.build_query(args, resources)
    # query.split_results = True
    # print(f"webapp.views.query.query:search_query={search_query}")
    # response = bus.ctx.search_service.search_with_query(search_query)


def statistics(resource_id: str, field: str, ctx: context.Context):
    check_resource_published(resource_id, ctx)
    with ctx.index_uow as uw:
        return uw.repo.statistics(resource_id, field)
