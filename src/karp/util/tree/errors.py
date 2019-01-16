class TreeException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "TreeException message='{}'".format(self.message)


class TooManyChildren(TreeException):
    def __init__(self, message):
        super().__init__(message)


class NoChild(TreeException):
    def __init__(self, message):
        super().__init__(message)


class ChildNotFound(TreeException):
    def __init__(self, message):
        super().__init__(message)
