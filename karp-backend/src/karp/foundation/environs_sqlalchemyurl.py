from sqlalchemy.engine.url import URL, make_url  # noqa: D100


def sqlalchemy_url(  # noqa: D103
    db_url: str,
    driver: str = None,
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
    database: str = None,
) -> URL:
    if db_url:
        return make_url(db_url)
    return URL.create(
        drivername=driver,
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
