from typing import Callable, Type  # noqa: F401
from fastapi import Depends  # noqa: F401
from sqlalchemy.orm import Session  # noqa: F401
from starlette.requests import Request

from karp.foundation.events import EventBus


def get_eventbus(request: Request) -> EventBus:
    return request.state.container.get(EventBus)
