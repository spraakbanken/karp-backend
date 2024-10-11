import enum
from typing import Optional


class ClientErrorCodes(enum.IntEnum):
    UNKNOWN_ERROR = 1
    ENTRY_NOT_FOUND = 30
    ENTRY_NOT_VALID = 32
    VERSION_CONFLICT = 33
    DB_INTEGRITY_ERROR = 61
    SEARCH_INCOMPLETE_QUERY = 81


class KarpError(Exception):
    def __init__(self, message: str, code: Optional[int] = None, http_return_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or ClientErrorCodes.UNKNOWN_ERROR
        self.http_return_code = http_return_code
