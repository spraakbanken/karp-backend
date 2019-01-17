# Karp TNG backend

This in the next version of Karp backend

## Setup

This project uses [pipenv](https://pipenv.readthedocs.io/) and
[MariaDB](https://mariadb.org/).

1. Install pipenv
2. Run `pipenv install --dev` (skip --dev if deploying)
3. Install MariaDB and create a database
4. Setup environment variables:
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
2. `pipenv run karp-cli import --resource_id places --version 1 --data tests/data/places.json`
3. Do the same for `municipalities`
4. `pipenv run karp-cli publish --resource_id places --version 1`
4. `pipenv run karp-cli publish --resource_id municipalities --version 1`

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
