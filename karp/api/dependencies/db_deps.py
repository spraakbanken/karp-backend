from sqlalchemy.orm import Session
from starlette.requests import Request


def get_session(request: Request) -> Session:  # noqa: D103
    return request.state.session
