from karp.domain import errors, index
from karp.services import context


def check_resource_published(resource_id: str, ctx: context.Context):
    with ctx.resource_uow:
        resource = ctx.resource_uow.repo.by_resource_id(resource_id)
        if not resource:
            raise errors.ResourceNotFound(resource_id)
        if not resource.is_published:
            raise errors.ResourceNotPublished(resource_id)


def search_ids(resource_id: str, entry_ids: str, ctx: context.Context):
    check_resource_published(resource_id, ctx)
    with ctx.index_uow:
        return ctx.index_uow.repo.search_ids(resource_id, entry_ids)


def query(req: index.QueryRequest, ctx: context.Context):
    return {"hits": [], "total": 0, "distribution": {}}
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
    return {"hits": [], "total": 0, "distribution": {}}
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
