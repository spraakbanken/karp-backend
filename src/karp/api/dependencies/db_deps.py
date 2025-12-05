from sqlalchemy.orm import Session
from starlette.requests import Request


def get_session(request: Request) -> Session:
    return request.state.session
