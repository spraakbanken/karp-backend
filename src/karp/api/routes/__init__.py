from karp.api.routes import (
    config_api,
    entries_api,
    history_api,
    query_api,
    resources_api,
    resources_api_v7,
    stats_api,
)


def register_routes(router, api_version=None):

    router.include_router(
        entries_api.router,
        prefix="/entries",
    )

    router.include_router(
        history_api.router,
        prefix="/history",
        tags=["History"],
    )
    router.include_router(
        query_api.router,
        prefix="/query",
        tags=["Searching"],
    )

    if api_version == "7":
        router.include_router(
            resources_api_v7.router,
            prefix="/resources",
            tags=["Resources"],
        )
    else:
        router.include_router(
            resources_api.router,
            prefix="/resources",
            tags=["Resources"],
        )
    router.include_router(
        stats_api.router,
        prefix="/stats",
        tags=["Statistics"],
    )
    router.include_router(
        config_api.router,
        prefix="/config",
        tags=["Configuration"],
    )
