import json

from typing import List
from typing import Dict


class ResourceConfig(object):
    def __init__(self, config: Dict) -> None:
        self.config: Dict = config

    def __repr__(self):
        return "ResourceConfig(config={})".format(json.dumps(self.config))

    def default_sort(self) -> str:
        return ""

    def get_fields(self) -> List[str]:
        return []

    def is_protected(self, mode: str, fields: List[str]) -> bool:
        print(__name__)
        print(repr(self.config))
        if "protected" in self.config:
            if mode in self.config["protected"]:
                # mode was found
                return self.config["protected"][mode]

        if mode == "read":
            return False
        else:
            return True
