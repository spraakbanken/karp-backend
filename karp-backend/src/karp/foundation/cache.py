class Cache(dict):
    """
    Implements a cache.

    The first time a key is looked up in the cache, a user-defined function is
    called to compute the value. If the same key is looked up again, the cached
    value is returned.

    The class inherits from dict so all dictionary methods are available.
    In particular, you can use cache.clear() to invalidate the cache.
    """

    def __init__(self, get):
        """
        When looking up cache[key], if key is not present in the cache,
        then get(key) will be called to compute the value.
        """

        self._get = get

    def __getitem__(self, key):
        if key not in self:
            self[key] = self._get(key)
        return super().__getitem__(key)
