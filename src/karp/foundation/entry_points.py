from typing import Iterable

try:
    from importlib.metadata import EntryPoint
    from importlib.metadata import entry_points as _entry_points
except ImportError:
    from importlib_metadata import EntryPoint  # type: ignore
    from importlib_metadata import entry_points as _entry_points  # type: ignore

import logging
import sys

logger = logging.getLogger(__name__)


def entry_points(group_name: str) -> Iterable[EntryPoint]:
    logger.debug("Loading %s", group_name)
    if sys.version_info.minor < 10:  # noqa: YTT204
        return _entry_points().get(group_name) or []
    else:
        return _entry_points(group=group_name) or []
