import functools
from flask import request

from karp.auth.authenticator import Authenticator


class Auth:

    def __init__(self):
        self.impl = Authenticator()

    def authorization(self, level):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                user = self.impl.authenticate(request)
                self.impl.authorize(level, user, kwargs)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def set_authenticator(self, authenticator):
        self.impl = authenticator


auth = Auth()
