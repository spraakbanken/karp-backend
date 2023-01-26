"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from fastapi import APIRouter, Depends, Response, status

from karp.webapp import schemas


router = APIRouter(tags=["Health"])


@router.get("/", response_model=schemas.SystemMonitorResponse, include_in_schema=False)
def perform_health_check():
    return {"database": "ok"}


def init_app(app):
    app.include_router(router)
