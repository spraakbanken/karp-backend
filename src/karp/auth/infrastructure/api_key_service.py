"""Module for API key authentication."""

import uuid
from typing import List

from injector import inject
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from karp.auth.domain.errors import ApiKeyError
from karp.auth.domain.user import User
from karp.lex.infrastructure.sql.models import ApiKeyModel

# this is how the JWT generation is set up oon SB-auth servers
# the API keys do not need to use the same format, but do this for now
levels = {
    "READ": 10,
    "WRITE": 100,
    "ADMIN": 1000,
}


def _generate_api_key() -> uuid.UUID:
    return uuid.uuid4()


class APIKeyService:
    @inject
    def __init__(self, session: Session):
        self.session = session

    def create_api_key(self, username, resources: List[str], level: str):
        api_key = _generate_api_key()
        num_level = levels[level]
        permissions = {resource: num_level for resource in resources}
        new_key = ApiKeyModel(username=username, api_key=api_key, permissions=permissions)
        self.session.add(new_key)
        self.session.commit()
        return api_key

    def delete_api_key(self, api_key):
        api_key_obj = self._get_api_key(api_key)
        self.session.delete(api_key_obj)
        self.session.commit()

    def authenticate(self, api_key: str) -> User:
        try:
            api_key_obj = self._get_api_key(api_key)
            user = User(api_key_obj.username, api_key_obj.permissions, levels)
            return user
        except NoResultFound:
            raise ApiKeyError() from None

    def list_keys(self):
        keys = self.session.execute(select(ApiKeyModel)).all()
        for key in keys:
            yield {
                "api_key": key[0].api_key,
                "username": key[0].username,
                "permissions": key[0].permissions,
            }

    def _get_api_key(self, api_key):
        rows = self.session.execute(select(ApiKeyModel).where(ApiKeyModel.api_key == api_key)).one()
        return rows[0]
