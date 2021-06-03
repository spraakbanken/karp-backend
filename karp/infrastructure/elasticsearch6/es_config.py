from starlette.config import Config as StarletteConfig
from starlette.datastructures import CommaSeparatedStrings

config = StarletteConfig(".env")


ELASTICSEARCH_HOST = config(
    "ELASTICSEARCH_HOST", cast=CommaSeparatedStrings, default=None
)
