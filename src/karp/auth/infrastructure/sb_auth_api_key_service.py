import json
import urllib
from typing import Any, Final, Mapping

from karp.auth.domain.errors import ApiKeyError
from karp.auth.domain.user import User
from karp.main.config import env

_sbauth_api_key: Final[str] = env("SBAUTH_API_KEY", None)
_sbauth_url: Final[str] = env("SBAUTH_URL", None)


def authenticate(api_key) -> Mapping[str, Any]:
    """
    Calls sb auth API to check what permissions the given API key has. The
    API uses the same format for permissions and levels as JWT / Karp red does internally.
    """
    headers = {
        "Authorization": f"apikey {_sbauth_api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({"apikey": api_key})
    response = post(_sbauth_url, headers, data)
    data = json.loads(response)
    permissions = data["scope"]["lexica"]
    user = User(data["user"]["sub"], permissions, data["levels"])
    return user


def post(url: str, headers: Mapping[str, object], payload: str) -> Mapping[str, Any]:
    req = urllib.request.Request(
        url=url,
        data=payload.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status != 200:
                raise ApiKeyError()
            body_bytes = resp.read()
            body_text = body_bytes.decode("utf-8")
            return body_text
    except urllib.error.HTTPError as e:
        raise ApiKeyError() from e
