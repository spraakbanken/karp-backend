from karp.lex_infrastructure import SqlResourceUnitOfWork  # noqa: F401
from karp.lex_infrastructure.repositories import SqlResourceRepository  # noqa: F401
from sqlalchemy.orm import Session
from starlette.requests import Request


def get_session(request: Request) -> Session:  # noqa: D103
    return request.state.session
