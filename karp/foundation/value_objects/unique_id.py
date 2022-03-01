"""Handle of unique ids.

Borrowed from https://bitbucket.org/sixty-north/d5-kanban-python
"""
import uuid
import ulid
import typing
try:
    import fastuuid  # type: ignore
except ModuleNotFoundError:
    fastuuid = None


def _make_unique_id() -> uuid.UUID:
    """Make a new UniqueId."""
    return ulid.new().uuid
    # return UniqueId(uuid.uuid4())


if fastuuid is not None:
    make_unique_id = fastuuid.uuid4
    UniqueId = fastuuid.UUID
    UniqueIdType = (fastuuid.UUID, uuid.UUID)
    typing_UniqueId = typing.Union[fastuuid.UUID, uuid.UUID]
else:
    make_unique_id = _make_unique_id
    UniqueId = uuid.UUID
    UniqueIdType = uuid.UUID
    typing_UniqueId = uuid.UUID
# class UniqueId:
#     """A UUID-based unique id with global formatting control.

#     When used in format specifiers the number of leading characters
#     of the UUID can be specified:

#         message = "The id={:6}".format(my_unique_id)

#     If not specified the globally configured format length will be
#     used. The global format length can be set by adjusting the
#     abbreviated_length class attribute. Setting this value to None
#     (the default) disables global format abbreviation.
#     """

#     abbreviated_length = None

#     @classmethod
#     def from_hex(cls, hex_str):
#         """Construct a UniqueId from a hex string representation of a UUID."""
#         return cls(uuid.UUID(hex=hex_str))

#     def __init__(self, the_uuid):
#         """Instantiate a UniqueId using a existing UUID object.

#         To create UniqueIds with fresh UUIDs call the make_unique_id()
#         factory function instead.

#         Args:
#             the_uuid: A UUID object.
#         """
#         self._uuid = the_uuid

#     def __eq__(self, rhs):
#         if not isinstance(rhs, UniqueId):
#             return NotImplemented
#         return self._uuid == rhs._uuid

#     def __ne__(self, rhs):
#         if not isinstance(rhs, UniqueId):
#             return NotImplemented
#         return self._uuid != rhs._uuid

#     def __hash__(self):
#         return hash(self._uuid)

#     def __repr__(self):
#         return self._uuid.hex

#     def __format__(self, format_spec):
#         if not format_spec:
#             return repr(self)[: UniqueId.abbreviated_length]
#         try:
#             format_abbrev_length = int(format_spec)
#         except ValueError:
#             raise TypeError(
#                 "UniqueId format spec {!r} is not an integer length".format(format_spec)
#             )
#         return repr(self)[:format_abbrev_length]
