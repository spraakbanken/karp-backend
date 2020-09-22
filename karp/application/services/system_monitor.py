from typing import Tuple

from karp.database import db


def check_database_status() -> Tuple[bool, str]:
    is_database_working = True
    output = "database is ok"

    try:
        # to check database we will execute raw query
        db.engine.execute("SELECT 1")
    except Exception as e:
        output = str(e)
        is_database_working = False

    return is_database_working, output
