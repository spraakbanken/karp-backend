from typing import List


class Resource(object):
    def __init__(self, sqlalchemy_class) -> None:
        self.cls = sqlalchemy_class

    def default_sort(self) -> str:
        return ""

    def get_fields(self) -> List[str]:
        return []

    def is_protected(self) -> bool:
        return self.protected
