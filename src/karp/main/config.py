import os
from typing import Callable

from sqlalchemy.engine import URL as DatabaseUrl
from sqlalchemy.engine import make_url

PROJECT_NAME = "Karp"
VERSION = "7.0.0"
API_PREFIX = "/"


class Env:
    def __init__(self):
        self.dotenv: dict[str, object] = {}

    def read_env(self, config_path: str):

        with open(config_path) as fp:
            for line in fp:
                if "=" not in line:
                    continue
                x = line.split("export ", maxsplit=1)
                if len(x) > 1:
                    x = x[1]
                else:
                    x = x[0]
                [key, val] = x.split("=", maxsplit=1)
                val = val.strip()
                if val[0] == '"' and val[-1] == '"':
                    val = val[1:-1]
                self.dotenv[key] = val

    def __call__[K](self, key, default_val: K | None = None, parser: Callable[[object], K] | None = None) -> K:
        # first check os env
        val = os.environ.get(key)
        if val is not None:
            return parser(val) if parser else val
        # then check .env
        val = self.dotenv.get(key)
        if val is not None:
            return parser(val) if parser else val
        return default_val

    def get[K](self, key, default_val: K) -> K:
        return self(key, default_val)

    def bool(self, key: str, default_val: bool) -> bool:
        return self(key, default_val, parser=bool)

    def int(self, key: str, default_val: int) -> int:
        return self(key, default_val, parser=int)


def load_env() -> Env:
    config_path = os.environ.get("CONFIG_PATH", ".env")
    env = Env()
    env.read_env(config_path)
    return env


def parse_database_name(env: Env) -> str:
    database_name = env("DB_DATABASE", "karp")
    if env("TESTING", None):
        database_name = env("DB_TEST_DATABASE", None) or f"{database_name}_test"
    return database_name


def parse_database_url(env: Env) -> DatabaseUrl:
    database_url = env("DATABASE_URL", None)
    if env.bool("TESTING", False):
        if database_test_url := env("DATABASE_TEST_URL", None):
            return make_url(database_test_url)
        elif database_url:
            return make_url(f"{database_url}_test")

    if database_url:
        return make_url(database_url)

    database_name = parse_database_name(env)

    return DatabaseUrl.create(
        drivername=env("DB_DRIVER", "mysql+pymysql"),
        username=env("DB_USER", None),
        password=env("DB_PASSWORD", None),
        host=env("DB_HOST", None),
        port=env.int("DB_PORT", None),
        database=database_name,
        query={"charset": "utf8mb4"},
    )


env = load_env()


DATABASE_URL = parse_database_url(env)
DATABASE_NAME = parse_database_name(env)
