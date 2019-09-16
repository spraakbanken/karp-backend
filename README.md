# Karp TNG backend

![](https://github.com/spraakbanken/karp-tng-backend/workflows/Build/badge.svg)

This in the next version of Karp backend

## Setup

This project uses [pipenv](https://pipenv.readthedocs.io/) and
[MariaDB](https://mariadb.org/).

1. Install pipenv
2. Run `pipenv install --dev` (skip --dev if deploying)
3. Install MariaDB and create a database
4. Setup environment variables (can be placed in a `.env` file in the root and then `pipenv run` sets those):
   ```
   export MARIADB_DATABASE=<name of database>
   export MARIADB_USER=<database user>
   export MARIADB_PASSWORD=<user's password>
   export MARIADB_HOST=localhost
   ```
5. Run `pipenv run alembic upgrade head` to initialize database
6. Run `pipenv run python wsgi.py` to start development server

    or `pipenv shell` when `python wsgi.py`

7. To setup Elasticsearch, download Elasticsearch 6.5.x and start it
8. Add environment variables
   ```
   export ES_ENABLED=true
   export ELASTICSEARCH_HOST=localhost:9200
   ```
## Create test resources

1. `pipenv run karp-cli create --config tests/data/config/places.json`
2. `pipenv run karp-cli import --resource_id places --version 1 --data tests/data/places.jsonl`
3. Do the same for `municipalities`
4. `pipenv run karp-cli publish --resource_id places --version 1`
4. `pipenv run karp-cli publish --resource_id municipalities --version 1`

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
