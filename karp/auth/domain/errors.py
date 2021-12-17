class AuthDomainError(Exception):
    '''Auth base exception.'''


class AuthError(AuthDomainError):
    pass


class ResourceNotFound(AuthError):
    pass
