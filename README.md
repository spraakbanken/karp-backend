# Karp TNG backend

[![Build Status](https://github.com/spraakbanken/karp-backend/workflows/Build/badge.svg)](https://github.com/spraakbanken/karp-backend/actions)

This in the version 6 of Karp backend, [for the legacy version (v5)](https://github.com/spraakbanken/karp-backend-v5).

## Setup

This project uses [poetry](https://python-poetry.org) and
[MariaDB](https://mariadb.org/).

1. Run `make install` or `make install-dev` for a develop-install (VENV_NAME defaults to .venv)
2. Install MariaDB and create a database
3. Setup environment variables (can be placed in a `.env` file in the root and then **?** `pipenv run` sets those):
   ```
   export MARIADB_DATABASE=<name of database>
   export MARIADB_USER=<database user>
   export MARIADB_PASSWORD=<user's password>
   export MARIADB_HOST=localhost
   export AUTH_JWT_PUBKEY_PATH=/path/to/pubkey
   ```
4. Activate the virtual environment by running: `source <VENV_NAME>/bin/activate` (VENV_NAME defaults to .venv)
5. Run `make init-db` to initialize database
   or `source <VENV_NAME>/bin/activate` and then `alembic upgrade head`
6. Run `make run-dev` to start development server

   or `source <VENV_NAME>/bin/activate` and then `python wsgi.py`

7. To setup Elasticsearch, download Elasticsearch 6.x or 7.x and start it
8. Install elasticsearch python libs for the right version
   1. If you use Elasticsearch 6.x, run `source <VENV_NAME>/bin/activate` and `pip install -e .[elasticsearch6]`
   2. If you use Elasticsearch 7.x, run `source <VENV_NAME>/bin/activate` and `pip install -e .[elasticsearch7]`
9. Add environment variables

```
export ES_ENABLED=true
export ELASTICSEARCH_HOST=localhost:9200
```

## Create test resources

1. `source <VENV_NAME>/bin/activate` and then:
2. `karp-cli create --config tests/data/config/places.json`
3. `karp-cli import --resource_id places --version 1 --data tests/data/places.jsonl`
4. Do the same for `municipalities`
5. `karp-cli publish --resource_id places --version 1`
6. `karp-cli publish --resource_id municipalities --version 1`

## Pre-processing data before publishing

Can be used to have less downtime, because sometimes the preprocessing may
be faster on another machine than the machine that talks to Elasticsearch.
Do `create` and `import` on both machines, with the same data. Use
machine 1 to preprocess and use result on machine 2.

1. Create resource and import data as usual.
2. Run `karp-cli preprocess --resource_id places --version 2 --filename places_preprocessed`

   `places_preprocessed` will contain a pickled dataset containing everything that is needed

3. Run `karp-cli publish_preprocessed --resource_id places --version 2 --data places_preprocessed`
4. Alternatively run `karp-cli reindex_preprocessed --resource_id places --data places_preprocessed`
   , if the resource was already published.

## Technologies

### Python

- Pipenv
- Flask
- SQLAlchemy
- Click
- Elasticsearch
- Elasticsearch DSL

### Databases

- MariaDB
- Elasticsearch

## Development

### Version handling

Version can be bumped with [`bumpversion`](https://pypi.org/project/bumpversion/).

Usage:

- Increase patch number `a.b.X => a.b.(X+1)`: `bumpversion patch`
- Increase minor number `a.X.c => a.(X+1).c`: `bumpversion minor`
- Increase major number `X.b.c => (X+1).b.c`: `bumpversion major`
- To custom version `a.b.c => X.Y.Z`: `bumpversion --new-version X.Y.Z`

`bumpversion` is configured in [`.bumpversion.cfg`](.bumpversion.cfg).

The version is changed in the following files:

- [`setup.py`](setup.py)
- [`src/karp/__init__.py`](src/karp/__init__.py)
- [`.bumpversion.cfg`](.bumpversion.cfg)
- [`doc/karp_api_spec.yaml`](doc/karp_api_spec.yaml)
