class InMemoryUnitOfWork:
    def __init__(self, **kwargs):  # noqa: ANN003, ANN204
        self.was_committed = False
        self.was_rolled_back = False
        self.was_closed = False

    def start(self):  # noqa: ANN201
        self.was_committed = False
        self.was_rolled_back = False
        self.was_closed = False
        return self

    def __enter__(self):  # noqa: ANN204
        self.was_committed = False
        self.was_rolled_back = False
        return self

    def _commit(self):  # noqa: ANN202
        self.was_committed = True

    def rollback(self):  # noqa: ANN201
        self.was_rolled_back = True

    def _close(self):  # noqa: ANN202
        self.was_closed = True
