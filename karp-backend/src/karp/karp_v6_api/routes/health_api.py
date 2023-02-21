"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""  # noqa: D212

from fastapi import APIRouter  # noqa: I001

from karp.karp_v6_api import schemas


router = APIRouter(tags=["Health"])


@router.get("/", response_model=schemas.SystemMonitorResponse, include_in_schema=False)
def perform_health_check():  # noqa: ANN201, D103
    return {"database": "ok"}


def init_app(app):  # noqa: ANN201, D103
    app.include_router(router)
