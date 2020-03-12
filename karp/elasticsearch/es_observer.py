from karp.util.notifier import Observer


class OnPublish(Observer):
    def update(self, *, alias_name: str, index_name: str, **kwargs):
        pass
