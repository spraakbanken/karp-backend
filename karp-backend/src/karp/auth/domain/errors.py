class AuthError(Exception):  # noqa: D100
    """Auth base exception."""


class ResourceNotFound(AuthError):  # noqa: D101
    pass


class TokenError(AuthError):
    """General token error."""


class ExpiredToken(TokenError):
    """The given token has expired."""


class InvalidTokenSignature(TokenError):  # noqa: D101
    pass


class InvalidTokenAudience(TokenError):  # noqa: D101
    pass


class InvalidTokenPayload(TokenError):  # noqa: D101
    pass
