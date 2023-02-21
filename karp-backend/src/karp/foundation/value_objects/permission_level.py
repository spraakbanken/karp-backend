from enum import Enum  # noqa: D100


class PermissionLevel(str, Enum):  # noqa: D101
    write = "WRITE"
    read = "READ"
    admin = "ADMIN"
