class Token:  # noqa: D100, D101
    def __init__(self, _type, value=None):  # noqa: D107, ANN204, ANN001
        self.type = _type
        self.value = value
