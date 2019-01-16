# from karp import errors


class SearchError(Exception):
    def __init__(self, message):
        super().__init__(message)


class IncompleteQuery(SearchError):
    def __init__(self, message):
        super().__init__(message)


class ParseError(SearchError):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __repr__(self) -> str:
        return "ParseError message='{}'".format(self.msg)


class SyntaxError(ParseError):
    def __init__(self, msg: str):
        super().__init__(msg)

    def __repr__(self) -> str:
        return "SyntaxError message='{}'".format(self.msg)
