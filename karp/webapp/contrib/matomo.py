import logging
from urllib.parse import urlunparse

from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp


logger = logging.getLogger(__name__)


class MatomoMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, idsite: str, matomo_url: str) -> None:
        super().__init__(app)
        self.idsite = idsite
        self.matomo_url = matomo_url

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        headers = {}
        for k, v in request.headers.items():
            headers[k.lower()] = v
        scope = request.scope
        host, port = scope['server']
        url = urlunparse(
            (
                str(scope['scheme']),
                f'{host}:{port}',
                str(scope['path']),
                '',
                str(scope['query_string']),
                '',
            )
        )
        logger.info(
            'got request',
            extra={
                'client': request.scope['client'],
                'server': request.scope['server'],
                'url': url,
                'headers': headers,
            }
        )
        response = await call_next(request)
        return response
