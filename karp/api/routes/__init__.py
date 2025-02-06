from fastapi import APIRouter  # noqa: I001

from karp.api.routes import (
    entries_api,
    history_api,
    query_api,
    resources_api,
    stats_api,
)


router = APIRouter()


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
