import enum
from typing import Optional


class ClientErrorCodes(enum.IntEnum):
    UNKNOWN_ERROR = 1
    ENTRY_NOT_FOUND = 30
    ENTRY_NOT_VALID = 32
    VERSION_CONFLICT = 33
    DB_INTEGRITY_ERROR = 61

    QUERY_PARSE_ERROR = 81
    SORT_ERROR = 82
    INCOMPATIBLE_RESOURCES = 83
    FIELD_DOES_NOT_EXIST = 84


class KarpError(Exception):
    def __init__(self, message: str, code: Optional[int] = None, http_return_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or ClientErrorCodes.UNKNOWN_ERROR
        self.http_return_code = http_return_code


class UserError(Exception):
    def __init__(self, message: str | dict, code: enum.IntEnum | None = None):
        super().__init__()
        self.message = message
        self.code = code

    def to_dict(self):
        if isinstance(self.message, dict):
            r = self.message
        else:
            r = {"message": self.message}
        if self.code:
            r["errorCode"] = int(self.code)
        return {"detail": r}


class QueryParserError(UserError):
    def __init__(self, failing_query: str, error_description: str) -> None:
        super().__init__(
            message={
                "failing_query": failing_query,
                "error_description": error_description,
                "message": "Error in query",
            },
            code=ClientErrorCodes.QUERY_PARSE_ERROR,
        )


class SortError(UserError):
    def __init__(self, resource_ids: list[str], sort_value: str | None = None):
        super().__init__(
            message=f"You can't sort by field '{sort_value}' for resource '{', '.join(resource_ids)}'",
            code=ClientErrorCodes.SORT_ERROR,
        )


class FieldDoesNotExist(UserError):
    def __init__(self, resource_ids: list[str], field: str):
        super().__init__(
            message=f'Field "{field}" does not exist in resource(s): "{", ".join(resource_ids)}"',
            code=ClientErrorCodes.FIELD_DOES_NOT_EXIST,
        )


class IncompatibleResources(UserError):
    def __init__(self, field: str):
        super().__init__(
            message=f'Resources have different settings for field: "{field}"',
            code=ClientErrorCodes.INCOMPATIBLE_RESOURCES,
        )
