from sqlalchemy import types  # noqa: D100, I001
import ulid


class ULIDType(types.TypeDecorator):  # noqa: D101
    impl = types.CHAR(26)

    cache_ok = True

    python_type = ulid.ULID

    @staticmethod
    def _coerce(value):  # noqa: ANN001, ANN205
        if value and not isinstance(value, ulid.ULID):
            value = ulid.parse(value)
        return value

    def process_bind_param(self, value, dialect):  # noqa: ANN201, D102, ANN001
        if value is None:
            return value

        if not isinstance(value, ulid.ULID):
            value = self._coerce(value)

        return value.str

    def process_result_value(self, value, dialect):  # noqa: ANN201, D102, ANN001
        return value if value is None else ulid.from_str(value)
