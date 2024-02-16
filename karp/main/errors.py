import enum  # noqa: D100
from typing import IO, Optional

NoIndexModuleConfigured = 10


class ClientErrorCodes(enum.IntEnum):  # noqa: D101
    UNKNOWN_ERROR = 1
    ENTRY_NOT_FOUND = 30
    ENTRY_NOT_VALID = 32
    VERSION_CONFLICT = 33
    DB_INTEGRITY_ERROR = 61
    SEARCH_INCOMPLETE_QUERY = 81


class KarpError(Exception):  # noqa: D101
    def __init__(  # noqa: D107
        self, message: str, code: Optional[int] = None, http_return_code: int = 400
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or ClientErrorCodes.UNKNOWN_ERROR
        self.http_return_code = http_return_code


class UpdateConflict(KarpError):  # noqa: D101
    def __init__(self, diff):  # noqa: D107, ANN204
        super().__init__(
            "Version conflict. Please update entry.",
            code=ClientErrorCodes.VERSION_CONFLICT,
        )
        self.error_obj = {"diff": diff, "errorCode": self.code, "error": self.message}
