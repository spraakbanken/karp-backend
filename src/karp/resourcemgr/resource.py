import json

from typing import List
from typing import Dict


class Resource(object):
    def __init__(self, model: Dict, config: Dict, version: int) -> None:
        self.model = model
        self.config = config
        self.version = version

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

    def has_format_query(self, format: str) -> bool:
        return True

    def id(self) -> str:
        return self.config['resource_id']
