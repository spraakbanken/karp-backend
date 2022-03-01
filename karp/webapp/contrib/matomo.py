import logging
import random
import urllib.parse
from urllib.parse import urlunparse

import urllib3
import urllib3.exceptions

from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp


logger = logging.getLogger(__name__)

http = urllib3.PoolManager()


class MatomoMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, idsite: str, matomo_url: str, *, assume_https: bool = True) -> None:
        super().__init__(app)
        self.idsite = idsite
        self.matomo_url = matomo_url
        self.assume_https = assume_https

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        headers = {}
        for k, v in request.headers.items():
            headers[k.lower()] = v
        scope = request.scope
        if 'x-forwarded-server' in headers:
            server = headers['x-forwarded-server']
        else:
            host, port = scope['server']
            server = f'{host}:{port}'
        root_path = scope.get('root_path')
        path = scope['path']
        if root_path:
            path = f'{root_path}{path}'
        url = urlunparse(
            (
                'https' if self.assume_https else str(scope['scheme']),
                server,
                path,
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

        tracking_params = urllib.parse.urlencode(
            {
                'idsite': self.idsite,
                'url': url,
                'rec': 1,
                'rand': random.getrandbits(32),
                'apiv': 1,

            }
        )
        tracking_url = f'{self.matomo_url}?{tracking_params}'
        try:
            http.request(
                'GET',
                tracking_url
            )
        except urllib3.exceptions.HTTPError:
            logger.exception('Error tracking view')
        return response
