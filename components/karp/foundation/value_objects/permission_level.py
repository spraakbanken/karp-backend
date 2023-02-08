from enum import Enum


class PermissionLevel(str, Enum):
    write = "WRITE"
    read = "READ"
    admin = "ADMIN"
