from typing import Dict, Optional

from karp.domain.models.entry import Entry, create_entry
from karp.domain.models.resource import Resource


def create_entry_from_dict(
    resource: Resource, raw: Dict, user: str = None, message: Optional[str] = None
) -> Entry:
    return create_entry(
        resource.id_getter()(raw), raw, last_modified_by=user, message=message
    )
