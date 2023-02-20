class QueryDSLError(Exception):  # noqa: D100, D101
    def __init__(self, message):  # noqa: D107, ANN204
        super().__init__(message)


class ParseError(QueryDSLError):  # noqa: D101
    def __init__(self, message: str) -> None:  # noqa: D107
        super().__init__(message)

    def __repr__(self) -> str:  # noqa: D105
        return f"ParseError message='{self}'"


class SyntaxError(ParseError):  # noqa: A001, D101
    def __init__(self, message: str):  # noqa: D107, ANN204
        super().__init__(message)

    def __repr__(self) -> str:  # noqa: D105
        return f"SyntaxError message='{str(self)}'"
