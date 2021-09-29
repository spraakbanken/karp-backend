import logging
from typing import Optional

from karp import bootstrap
from karp.domain import model
# from karp.auth.auth import auth
from karp.errors import ClientErrorCodes, KarpError

bus = bootstrap.bootstrap()


logger = logging.getLogger("karp")
