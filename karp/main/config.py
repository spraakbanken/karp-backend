import os

import environs
from sqlalchemy.engine import URL as DatabaseUrl
from sqlalchemy.engine import make_url

PROJECT_NAME = "Karp"
VERSION = "6.2.0"
API_PREFIX = "/"


def load_env() -> environs.Env:
    config_path = os.environ.get("CONFIG_PATH", ".env")
    env = environs.Env()
    env.read_env(config_path)
    return env


def parse_database_name(env: environs.Env) -> str:
    database_name = env("DB_DATABASE", "karp")
    if env("TESTING", None):
        database_name = env("DB_TEST_DATABASE", None) or f"{database_name}_test"
    return database_name


def parse_database_url(env: environs.Env) -> DatabaseUrl:
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
