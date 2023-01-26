from fastapi import APIRouter

from karp.webapp.routes import (
    entries_api,
    health_api,
    history_api,
    query_api,
    resources_api,
    stats_api,
)


router = APIRouter()


router.include_router(
    entries_api.router,
    prefix="/entries",
    tags=["Entries"],
)
router.include_router(health_api.router, prefix="/healthz")
router.include_router(
    history_api.router,
    prefix="/history",
    tags=["Entries", "History"],
)
router.include_router(
    query_api.router,
    prefix="/query",
    tags=["Querying"],
)
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
