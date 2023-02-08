# Karp backend

[![Build Status](https://github.com/spraakbanken/karp-backend/workflows/Build/badge.svg)](https://github.com/spraakbanken/karp-backend/actions)
[![CodeScene Code Health](https://codescene.io/projects/24151/status-badges/code-health)](https://codescene.io/projects/24151)
[![codecov](https://codecov.io/gh/spraakbanken/karp-backend/branch/main/graph/badge.svg?token=iwTQnHKOpm)](https://codecov.io/gh/spraakbanken/karp-backend)

This is a monorepo containing the following projects:

- **karp-lex-core** [![PyPI version](https://badge.fury.io/py/karp-lex-core.svg)](https://badge.fury.io/py/karp-lex-core)

- **karp-backend** [![PyPI version](https://badge.fury.io/py/karp-backend.svg)](https://badge.fury.io/py/karp-backend)

This is the version 6 of Karp backend, [for the legacy version (v5)](https://github.com/spraakbanken/karp-backend-v5).

## Development

This project uses [poetry](https://python-poetry.org) and the plugins `poetry-multiproject-plugin` and `poetry-polylith-plugin`.

The metadata to each lives in `projects/<project-name>` which include code from at least 1 bases (from `bases`) and 0 or more
components (from `components`).

Provided are both a Makefile and a Justfile. They should behave the same.

### Getting started

1. First clone this repo: `git clone` or `gh repo clone` (if using github-cli).

2. Install dependencies:
   1. `just dev` (or `just install-dev`)
   2. `make dev` (or `make install-dev`)

3. Install MariaDB and create a database

4. Setup environment variables (can be placed in a `.env` file in the root and then **?** `poetry run` sets those):
   ```
   export DB_DATABASE=<name of database>
   export DB_USER=<database user>
   export DB_PASSWORD=<user's password>
   export DB_HOST=localhost
   export AUTH_JWT_PUBKEY_PATH=/path/to/pubkey
   ```
4. Activate the virtual environment by running: `poetry shell`
5. Run `karp-cli db up` to initialize database
6. Run `make serve` or `make serve-w-reload` to start development server

   or `poetry shell` and then `uvicorn --factory karp.karp_v6_api.main:create_app`

7. To setup Elasticsearch, download Elasticsearch 6.x and start it
8. Install elasticsearch python libs for the right version
   1. If you use Elasticsearch 6.x, run `source <VENV_NAME>/bin/activate` and `pip install -e .[elasticsearch6]`
9. Add environment variables

```
export ES_ENABLED=true
export ELASTICSEARCH_HOST=localhost:9200
export SEARCH_CONTEXT=es6_search_service
```

## Create test resources

1. `poetry shell` and then:
2. `karp-cli entry-repo create assets/testing/config/places.json`
3. `karp-cli resource create assets/testing/config/places.json`
4. `karp-cli entries add places assets/testing/data/places.json`
5. Do the same for `municipalities`
6. `karp-cli resource publish places`
7. `karp-cli resource publish municipalities`

## Pre-processing data before publishing

** TODO: review this **
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

- Python >= 3.10
- Poetry >= 1.3
- FastAPI
- SQLAlchemy
- Typer
- Elasticsearch
- Elasticsearch DSL

### Databases

- MariaDB
- Elasticsearch

## Development

### Version handling

Version can be bumped with [`bump2version`](https://pypi.org/project/bump2version/).

Usage:

- Increase patch number `a.b.X => a.b.(X+1)`: `make bumpversion` or `bumpversion patch`
- Increase minor number `a.X.c => a.(X+1).0`: `make bumpversion-minor` or `bumpversion minor`
- Increase major number `X.b.c => (X+1).0.0`: `make bumpversion-major` or `bumpversion major`
- To custom version `a.b.c => X.Y.Z`: `bumpversion --new-version X.Y.Z`

`bumpversion` is configured in [`.bumpversion.cfg`](.bumpversion.cfg).

The version is changed in the following files:

- [`setup.py`](setup.py)
- [`src/karp/__init__.py`](src/karp/__init__.py)
- [`.bumpversion.cfg`](.bumpversion.cfg)
- [`doc/karp_api_spec.yaml`](doc/karp_api_spec.yaml)
