import os

import environs
from sqlalchemy.engine import url as sa_url


def load_env() -> environs.Env:
    config_path = os.environ.get("CONFIG_PATH", ".env")
    print(f"loading config from '{config_path}'")
    env = environs.Env()
    env.read_env(config_path)
    return env


def parse_sqlalchemy_url(env: environs.Env) -> sa_url.URL:
    db_url = env('DB_URL', None)
    if db_url:
        return sa_url.make_url(db_url)
    database = env('DB_DATABASE', None)
    if env('TESTING', None):
        database = env('DB_TEST_DATABASE', None) or f'test_{database}'
    return sa_url.URL.create(
        drivername=env('DB_DRIVER', 'mysql+pymysql'),
        username=env('DB_USER', None),
        password=env('DB_PASSWORD', None),
        host=env('DB_HOST', None),
        port=env.int('DB_PORT', None),
        database=database,
        query={'charset': 'utf8mb4'}
    )
