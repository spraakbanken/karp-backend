from enum import Enum


class PermissionLevel(str, Enum):
    write = "write"
    read = "read"
    admin = "admin"
