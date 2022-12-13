from sqlalchemy import types
import ulid


class ULIDType(types.TypeDecorator):
    impl = types.CHAR(26)

    cache_ok = True

    python_type = ulid.ULID

    @staticmethod
    def _coerce(value):
        if value and not isinstance(value, ulid.ULID):
            value = ulid.parse(value)
        return value

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, ulid.ULID):
            value = self._coerce(value)

        return value.str

    def process_result_value(self, value, dialect):
        return value if value is None else ulid.from_str(value)
