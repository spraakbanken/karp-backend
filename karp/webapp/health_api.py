"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from fastapi import APIRouter, Response, status

from karp.application import schemas
from karp.application.services.system_monitor import check_database_status


router = APIRouter()

from .app_config import bus


@router.get("/healthz", response_model=schemas.SystemMonitorResponse)
def perform_health_check(response: Response):
    db_status = check_database_status(bus.ctx)
    if not db_status:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return {"database": db_status.message}


def init_app(app):
    app.include_router(router)
