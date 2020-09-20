import json

from typing import List, Dict, Optional

from karp.database import ResourceDefinition


class Resource:
    def __init__(
        self,
        model,
        history_model,
        resource_def: ResourceDefinition,
        version: int,
        config: Optional[Dict] = None,
    ) -> None:
        self.model = model
        self.history_model = history_model
        if config:
            self.config = config
        else:
            self.config = json.loads(resource_def.config_file)
        self.entry_json_schema = json.loads(resource_def.entry_json_schema)
        self.active = resource_def.active
        self.version = version

    def __repr__(self):
        return "ResourceConfig(config={})".format(json.dumps(self.config))

    def default_sort(self) -> List[str]:
        default_sort = self.config["sort"]
        if isinstance(default_sort, list):
            return default_sort
        return [default_sort]

    def get_fields(self) -> List[str]:
        return []

    def is_protected(self, mode: str, fields: List[str]) -> bool:
        print(__name__)
        print(repr(self.config))
        if "protected" in self.config:
            if mode in self.config["protected"]:
                # mode was found
                return self.config["protected"][mode]

        return mode != "read"

    def has_format_query(self, format: str) -> bool:
        return True

    @property
    def id(self) -> str:
        return self.config["resource_id"]
