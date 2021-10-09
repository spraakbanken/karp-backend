from karp import errors


class QueryDSLError(errors.KarpError):
    def __init__(self, message):
        super().__init__(message)


class ParseError(QueryDSLError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

    def __repr__(self) -> str:
        return "ParseError message='{}'".format(self.message)


class SyntaxError(ParseError):
    def __init__(self, message: str):
        super().__init__(message)

    def __repr__(self) -> str:
        return "SyntaxError message='{}'".format(self.message)
