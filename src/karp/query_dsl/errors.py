from karp import errors


class QueryDSLError(errors.KarpError):
    def __init__(self, message):
        super().__init__(message)


class ParseError(QueryDSLError):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)

    def __repr__(self) -> str:
        return "ParseError message='{}'".format(self.msg)


class SyntaxError(ParseError):
    def __init__(self, msg: str):
        super().__init__(msg)

    def __repr__(self) -> str:
        return "SyntaxError message='{}'".format(self.msg)
