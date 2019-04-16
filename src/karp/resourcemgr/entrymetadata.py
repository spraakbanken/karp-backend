from typing import Optional
from datetime import datetime, timezone


class EntryMetadata:

    @staticmethod
    def init_from_model(x):
        return EntryMetadata(x.user_id, version=x.version, last_modified=x.timestamp)

    def __init__(self, user_id: str, version: int=1, last_modified: Optional[datetime]=None):
        self.version = version
        self.last_modified = datetime.now(timezone.utc) if not last_modified else last_modified
        self.last_modified_by = user_id

    def to_dict(self):
        return {
            '_entry_version': self.version,
            '_last_modified': self.last_modified.timestamp(),
            '_last_modified_by': self.last_modified_by
        }
