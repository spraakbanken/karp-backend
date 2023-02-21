from karp.foundation.events import EventBus  # noqa: D100
from sqlalchemy.orm import Session  # noqa: F401
from starlette.requests import Request


def get_eventbus(request: Request) -> EventBus:  # noqa: D103
    return request.state.container.get(EventBus)
