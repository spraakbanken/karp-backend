class AuthDomainError(Exception):
    '''Auth base exception.'''


class AuthError(AuthDomainError):
    pass


class ResourceNotFound(AuthError):
    pass


class ExpiredJWTError(AuthDomainError):
    """The given JWT has expired."""


class GeneralJWTError(AuthDomainError):
    """General JWT error."""
