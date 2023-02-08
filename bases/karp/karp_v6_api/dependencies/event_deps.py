from typing import Callable, Type
from fastapi import Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from karp.foundation.events import EventBus


def get_eventbus(request: Request) -> EventBus:
    return request.state.container.get(EventBus)
