NoIndexModuleConfigured = 10


class ClientErrorCodes:
    RESOURCE_DOES_NOT_EXIST = 20
    RESOURCE_NOT_PUBLISHED = 21
    ENTRY_NOT_FOUND = 30
    ENTRY_NOT_CHANGED = 31
    ENTRY_NOT_VALID = 32
    VERSION_CONFLICT = 33
    EXPIRED_JWT = 40
    NOT_PERMITTED = 41
    BAD_PARAMETER_FORMAT = 50
    DB_GENERAL_ERROR = 60
    DB_INTEGRITY_ERROR = 61


class KarpError(Exception):

    def __init__(self, message: str, code: int = None, http_return_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_return_code = http_return_code


class ResourceNotFoundError(KarpError):

    def __init__(self, resource_id, version: int = None):
        super().__init__('Resource not found. ID: {resource_id}, version: {version}'. format(
            resource_id=resource_id,
            version=version
        ), ClientErrorCodes.RESOURCE_DOES_NOT_EXIST)


class EntryNotFoundError(KarpError):

    def __init__(
            self,
            resource_id,
            entry_id,
            entry_version=None,
            resource_version=None
    ):
        msg = 'Entry {entry_id} (version {entry_version}) not found. ID: {resource_id}, version: {resource_version}'
        super().__init__(msg. format(
            resource_id=resource_id,
            resource_version=resource_version if resource_version else 'latest',
            entry_id=entry_id,
            entry_version=entry_version if entry_version else 'latest'
        ), ClientErrorCodes.ENTRY_NOT_FOUND)


class UpdateConflict(KarpError):

    def __init__(self, diff):
        super().__init__('Version conflict. Please update entry.', code=ClientErrorCodes.VERSION_CONFLICT)
        self.error_obj = {
            'diff': diff,
            'errorCode': self.code,
            'error': self.message
        }
