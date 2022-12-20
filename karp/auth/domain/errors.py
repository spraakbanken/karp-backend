class AuthError(Exception):
    """Auth base exception."""


class ResourceNotFound(AuthError):
    pass


class TokenError(AuthError):
    """General token error."""


class ExpiredToken(TokenError):
    """The given token has expired."""


class InvalidTokenSignature(TokenError):
    pass


class InvalidTokenAudience(TokenError):
    pass


class InvalidTokenPayload(TokenError):
    pass
