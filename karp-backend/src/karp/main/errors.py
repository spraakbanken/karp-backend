import enum  # noqa: D100
from typing import IO, Optional

NoIndexModuleConfigured = 10


class ClientErrorCodes(enum.IntEnum):  # noqa: D101
    UNKNOWN_ERROR = 1
    RESOURCE_DOES_NOT_EXIST = 20
    RESOURCE_NOT_PUBLISHED = 21
    RESOURCE_CONFIG_NOT_VALID = 22
    RESOURCE_CONFIG_CANNOT_UPDATE = 23
    RESOURCE_ALREADY_PUBLISHED = 24
    ENTRY_NOT_FOUND = 30
    ENTRY_NOT_CHANGED = 31
    ENTRY_NOT_VALID = 32
    VERSION_CONFLICT = 33
    ENTRY_ID_MISMATCH = 34
    EXPIRED_JWT = 40
    NOT_PERMITTED = 41
    AUTH_GENERAL_ERROR = 49
    BAD_PARAMETER_FORMAT = 50
    DB_GENERAL_ERROR = 60
    DB_INTEGRITY_ERROR = 61
    PLUGIN_DOES_NOT_EXIT = 70
    SEARCH_GENERAL_ERROR = 80
    SEARCH_INCOMPLETE_QUERY = 81
    SEARCH_UNSUPPORTED_QUERY = 82
    SEARCH_UNSUPPORTED_FIELD = 83


class KarpError(Exception):  # noqa: D101
    def __init__(  # noqa: D107
        self, message: str, code: int = None, http_return_code: int = 400
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or ClientErrorCodes.UNKNOWN_ERROR
        self.http_return_code = http_return_code


class UserError(KarpError):  # noqa: D101
    pass


class ResourceNotFoundError(KarpError):  # noqa: D101
    def __init__(self, resource_id, version: int = None):  # noqa: D107, ANN204
        super().__init__(
            "Resource not found. ID: {resource_id}, version: {version}".format(
                resource_id=resource_id, version=version
            ),
            ClientErrorCodes.RESOURCE_DOES_NOT_EXIST,
        )


class ResourceInvalidConfigError(KarpError):  # noqa: D101
    def __init__(  # noqa: D107
        self, resource_id, config_file: IO, validation_error_msg: str
    ) -> None:
        msg_fmt = """
        Resource config is not valid.
        ID: {resource_id},
        config: {config_file},
        error: "{validation_error_msg}"
        """
        super().__init__(
            msg_fmt.format(
                resource_id=resource_id,
                config_file=config_file.name,
                validation_error_msg=validation_error_msg,
            ),
            ClientErrorCodes.RESOURCE_CONFIG_NOT_VALID,
        )


class ResourceConfigUpdateError(KarpError):  # noqa: D101
    def __init__(self, msg, resource_id, config_file: IO):  # noqa: D107, ANN204
        msg_fmt = """
        Cannot update config for resource.
        Message: '{msg}'
        ID: {resource_id},
        config: {config_file}"
        """
        super().__init__(
            msg_fmt.format(
                resource_id=resource_id,
                config_file=config_file.name,
                msg=msg,
            ),
            ClientErrorCodes.RESOURCE_CONFIG_CANNOT_UPDATE,
        )


class ResourceAlreadyPublished(KarpError):  # noqa: D101
    def __init__(self, resource_id: str):  # noqa: D107, ANN204
        super().__init__(
            f"Resource '{resource_id}' already published",
            code=ClientErrorCodes.RESOURCE_ALREADY_PUBLISHED,
        )


class EntryNotFoundError(KarpError):  # noqa: D101
    def __init__(  # noqa: D107, ANN204
        self,
        resource_id,
        entry_id,
        entry_version=None,
        resource_version=None,
    ):
        msg = "Entry '{entry_id}' (version {entry_version}) not found. resource_id: {resource_id}, version: {resource_version}"
        super().__init__(
            msg.format(
                resource_id=resource_id,
                resource_version=resource_version if resource_version else "latest",
                entry_id=entry_id,
                entry_version=entry_version if entry_version else "latest",
            ),
            ClientErrorCodes.ENTRY_NOT_FOUND,
        )


class UpdateConflict(KarpError):  # noqa: D101
    def __init__(self, diff):  # noqa: D107, ANN204
        super().__init__(
            "Version conflict. Please update entry.",
            code=ClientErrorCodes.VERSION_CONFLICT,
        )
        self.error_obj = {"diff": diff, "errorCode": self.code, "error": self.message}


class EntryIdMismatch(UserError):  # noqa: D101
    def __init__(self, new_entry_id: str, entry_id: str):  # noqa: D107, ANN204
        super().__init__(
            f"entry_id '{new_entry_id}' does not equal '{entry_id}'",
            code=ClientErrorCodes.ENTRY_ID_MISMATCH,
        )


class PluginNotFoundError(KarpError):  # noqa: D101
    def __init__(self, plugin_id: str, resource_id: str = None):  # noqa: D107, ANN204
        super().__init__(
            "Plugin '{plugin_id}' not found, referenced by '{resource_id}'".format(
                plugin_id=plugin_id, resource_id=resource_id if resource_id else "..."
            ),
            ClientErrorCodes.PLUGIN_DOES_NOT_EXIT,
        )


class IntegrityError(UserError):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        message: Optional[str] = None,
        *,
        key: Optional[str] = None,
        value: Optional[str] = None,
    ) -> None:
        if message is None:
            message = ""
        if key and value:
            message = f"The key '{key}' is not unique (value='{value}')."
        super().__init__(
            message,
            code=ClientErrorCodes.DB_INTEGRITY_ERROR,
        )
