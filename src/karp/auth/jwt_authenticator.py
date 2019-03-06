import jwt
import time

from .authenticator import Authenticator
from karp import get_resource_string
from karp.auth.user import User
import karp.resourcemgr as resourcemgr
from karp.errors import KarpError

jwt_key = get_resource_string('auth/pubkey.pem')


class JWTAuthenticator(Authenticator):

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        auth_token = None
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        if auth_token:
            user_token = jwt.decode(auth_token, key=jwt_key, algorithms=["RS256"])
            if user_token["exp"] < time.time():
                raise KarpError("The given jwt have expired")

            lexicon_permissions = {}
            if "scope" in user_token and "lexica" in user_token["scope"]:
                lexicon_permissions = user_token["scope"]["lexica"]
            return User(user_token['sub'], lexicon_permissions, user_token["levels"])

        return None

    def authorize(self, level, user, args):
        if 'resource_id' in args:
            resource_ids = [args['resource_id']]
        elif 'resource_ids' in args:
            resource_ids = args['resource_id'].split(',')
        elif 'resources' in args:
            resource_ids = args['resources'].split(',')
        else:
            return True

        for resource_id in resource_ids:
            if resourcemgr.is_protected(resource_id, level):
                if not user or user.permissions[resource_id] < user.levels[level]:
                    return False
        return True
