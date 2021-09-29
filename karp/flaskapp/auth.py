import functools

from flask import request  # pyre-ignore

from karp.auth.authenticator import Authenticator
from karp.errors import ClientErrorCodes, KarpError


class Auth:
    def __init__(self):
        self.impl = Authenticator()

    def authorization(self, level, add_user=False):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                user = self.impl.authenticate(request)
                if self.impl.authorize(level, user, kwargs):
                    if add_user:
                        return func(user, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                else:
                    raise KarpError(
                        "Not permitted", code=ClientErrorCodes.NOT_PERMITTED
                    )

            return wrapper

        return decorator

    def set_authenticator(self, authenticator):
        self.impl = authenticator


auth = Auth()
