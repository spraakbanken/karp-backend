import logging
import random
from re import I
from typing import Optional
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


def get_remote_address(req: Request) -> str:
    return req.scope["client"][0]


class MatomoMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        idsite: str,
        matomo_url: str,
        access_token: Optional[str] = None,
        *,
        assume_https: bool = True,
    ) -> None:
        super().__init__(app)
        self.idsite = idsite
        self.matomo_url = matomo_url
        self.assume_https = assume_https
        self._access_token = access_token

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        headers = {}
        for k, v in request.headers.items():
            headers[k.lower()] = v
        scope = request.scope
        if "x-forwarded-server" in headers:
            server = headers["x-forwarded-server"]
        else:
            host, port = scope["server"]
            server = f"{host}:{port}"
        root_path = scope.get("root_path")
        path = scope["path"]
        if root_path:
            path = f"{root_path}{path}"
        url = urlunparse(
            (
                "https" if self.assume_https else str(scope["scheme"]),
                server,
                path,
                "",
                str(scope["query_string"]),
                "",
            )
        )
        logger.info(
            "got request",
            extra={
                "client": request.scope["client"],
                "server": request.scope["server"],
                "url": url,
                "headers": headers,
            },
        )
        cip = get_remote_address(request)
        response = await call_next(request)

        params_that_require_token = {}
        if self._access_token:
            params_that_require_token = {"token_auth": self._access_token, "cip": cip}
        else:
            logger.warning("Not recording client ip", extra={"cip": cip})

        tracking_dict = {
            "idsite": self.idsite,
            "url": url,
            "rec": 1,
            "rand": random.getrandbits(32),
            "apiv": 1,
            "ua": headers.get("user-agent"),
            "lang": headers.get("accept-lang"),
            **params_that_require_token,
        }
        tracking_params = urllib.parse.urlencode(tracking_dict)
        tracking_url = f"{self.matomo_url}?{tracking_params}"
        try:
            logger.debug("Making tracking call", extra={"url": tracking_url})
            r = http.request("GET", tracking_url)
            logger.debug(
                "tracking call", extra={"status_code": r.status, "data": r.data}
            )
        except urllib3.exceptions.HTTPError:
            logger.exception("Error tracking view")
        return response
