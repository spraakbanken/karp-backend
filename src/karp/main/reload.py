import logging
import subprocess
from pathlib import Path

from karp.main import config
from karp.main.errors import KarpError

logger = logging.getLogger(__name__)


def call_resource_update_hook() -> int | None:
    """
    Calls the script given by RESOURCE_UPDATE_HOOK or `bin/reload` if no script is given
    """
    script = Path(config.env.get("RESOURCE_UPDATE_HOOK", "bin/reload"))

    # script can be relative to .env file, so also check BASE_PATH
    base_path = Path(config.env.get("BASE_PATH", "."))

    try:
        p = subprocess.run([script], check=False, cwd=base_path)
        logger.info(f"Successfully called {script}")
    except OSError as e:
        raise KarpError(f"Error when calling RESOURCE_UPDATE_HOOK script ({e.strerror})") from e
    return p.returncode
