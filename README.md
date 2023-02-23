# Karp backend

[![Build Status](https://github.com/spraakbanken/karp-backend/workflows/Build/badge.svg)](https://github.com/spraakbanken/karp-backend/actions)
[![CodeScene Code Health](https://codescene.io/projects/24151/status-badges/code-health)](https://codescene.io/projects/24151)
[![codecov](https://codecov.io/gh/spraakbanken/karp-backend/branch/main/graph/badge.svg?token=iwTQnHKOpm)](https://codecov.io/gh/spraakbanken/karp-backend)

This is a monorepo containing the following projects:

- **karp-lex-core** [![PyPI version](https://badge.fury.io/py/karp-lex-core.svg)](https://badge.fury.io/py/karp-lex-core)

- **karp-backend** [![PyPI version](https://badge.fury.io/py/karp-backend.svg)](https://badge.fury.io/py/karp-backend)

This is the version 6 of Karp backend, [for the legacy version (v5)](https://github.com/spraakbanken/karp-backend-v5).

## Development

This project uses [poetry](https://python-poetry.org).

The metadata and source-code to each project lives in `<project-name>`.

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
6. Run `make/just serve` or `make/just serve-w-reload` to start development server

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

Both [`Justfile`](Justfile) and [`Makefile`](Makefile) are provided, for `just` you can run `just --list` to list all recipes defined in the Justfile.

### Testing

The tests are organized in unit, integration and end-to-end tests.

`karp-lex-core` currently only has unit tests.

#### Unit tests
These test should have no infrastructure dependencies and should run fast.

Run them by:
- From repo root:
   - `just/make test` (or `just/make unit-tests`)
   - `just unit-tests-w-coverage` or `just cov-report=xml unit-tests-w-coverage`
   - `just test-w-coverage karp-backend/src/karp/tests/unit karp-lex-core/src/karp/lex_core/tests`
   - `make unit-tests-w-coverage` or `make cov_report=xml unit-tests-w-coverage`
   - `make all_tests="karp-backend/src/karp/tests/unit karp-lex-core/src/karp/lex_core/tests" test-w-coverage`
- From `karp-backend` root:
   - `just/make test`
   - `just test-w-coverage src/karp/tests/unit`
   - `make all_tests=src/karp/tests/unit test-w-coverage`
- From `karp-lex-core` root:
   - `just/make test`
   - `just/make test-w-coverage`


#### Integration tests
These test have some infrastructure dependencies and should run slower.

Run them by:
- From repo root:
   - `just/make integration-tests`
   - `just integration-tests-w-coverage` or `just cov-report=xml integration-tests-w-coverage`
   - `just test-w-coverage karp-backend/src/karp/tests/integration`
   - `make integration-tests-w-coverage` or `make cov_report=xml integration-tests-w-coverage`
   - `make all_tests=karp-backend/src/karp/tests/integration test-w-coverage`
- From `karp-backend` root:
   - `just/make test`
   - `just test-w-coverage src/karp/tests/integration`
   - `make all_tests=src/karp/tests/integration test-w-coverage`

#### End-to-end tests
These test have all infrastructure dependencies and should run slowest.

Run them by:
- From repo root:
   - `just/make e2e-tests`
   - `just e2e-tests-w-coverage` or `just cov-report=xml e2e-tests-w-coverage`
   - `just test-w-coverage karp-backend/src/karp/tests/e2e`
   - `make e2e-tests-w-coverage` or `make cov_report=xml e2e-tests-w-coverage`
   - `make all_tests=karp-backend/src/karp/tests/e2e test-w-coverage`
- From `karp-backend` root:
   - `just/make test`
   - `just test-w-coverage src/karp/tests/e2e`
   - `make all_tests=src/karp/tests/e2e test-w-coverage`

#### All tests
These test have all infrastructure dependencies and should run slowest.

Run them by:
- From repo root:
   - `just/make all-tests`
   - `just test-w-coverage` or `just cov-report=xml test-w-coverage`
   - `just all-tests-w-coverage`
   - `make test-w-coverage` or `make cov_report=xml test-w-coverage`
   - `make all-tests-w-coverage`
- From `karp-backend` root:
   - `just test src/karp/tests`
   - `make tests=src/karp/tests test`
   - `just test-w-coverage`
   - `make test-w-coverage`
- From `karp-lex-core` root:
   - `just/make test`
   - `just test-w-coverage`
   - `make test-w-coverage`


### Linting
Linting is done by [`ruff`](https://beta.ruff.rs/docs/).

Run with `just lint` or `make lint`. This can also be run in project folders.

Each project has different settings in `ruff.toml` [here](karp-backend/ruff.toml) and [here](karp-lex-core/ruff.toml).

Usual commands for `ruff` is:
- `ruff --fix <path>` tries to fix linting problems.
- `ruff --add-noqa <path>` add noqa:s (silence lint) to each line that needs

### Formatting
Formatting is done by `black`.

Run formatter with `just/make fmt`, check if formatting is needed `just/make check-fmt`.


### Type checking
Type checking is done by `mypy`

Currently only `karp-lex-core` is expected to pass type-checking.
The goal is that also `karp-backend` should pass type-checking.

### Continous Integration
This projects uses Github Actions to test and check the code.

- When pushing a commit to Github:
   - All tests are run and coverage is uploaded to [`codecov`](https://codecov.io/gh/spraakbanken/karp-backend).
   - All code is linted and expected to pass.
   - All code is checked if it is formatted.
   - All code is type-checked and for `karp-lex-core` it is expected to pass.
- All above also apply to Pull Requests.
- When a pull request is closed and merged the Pull Request title and body is written in each projects README.md.
- When a tag named `karp-lex-core-v*` is pushed a distribution for `karp-lex-core` is created and uploaded to [PyPi](https://pypi.org).
- When a tag named `karp-backend-v*` is pushed a distribution for `karp-backend` is created and uploaded to [PyPi](https://pypi.org).
- When anything is pushed the docs are built and published to [spraakbanken.github.io/karp-backend](https://spraakbanken.github.io/karp-backend).


### Version handling

Version can be bumped with [`bump2version`](https://pypi.org/project/bump2version/).

Usage for:

- Increase patch number `a.b.X => a.b.(X+1)`:
   - From repo root for project `<project>`
      - `just <project>/bumpversion`
      - `make project=<project> bumpversion`
   - From project root
      - `just bumpverision`
      - `make bumpversion`
      - `bump2version patch`
- Increase minor number `a.X.c => a.(X+1).0`:
   - From repo root for project `<project>`
      - `just <project>/bumpversion minor`
      - `make project=<project> part=minor bumpversion`
   - From project root
      - `just bumpverision minor`
      - `make part=minor bumpversion`
      - `bump2version minor`
- Increase major number `X.b.c => (X+1).0.0`:
   - From repo root for project `<project>`
      - `just <project>/bumpversion major`
      - `make project=<project> part=major bumpversion`
   - From project root
      - `just bumpverision major`
      - `make part=major bumpversion`
      - `bump2version major`
- To custom version `a.b.c => X.Y.Z`:
   - From repo root for project `<project>`
      - `just <project>/bumpversion "--new-version X.Y.Z"`
      - `make project=<project> part="--new-version X.Y.Z" bumpversion`
   - From project root
      - `just bumpverision "--new-version X.Y.Z"`
      - `make part="--new-version X.Y.Z" bumpversion`
      - `bumpversion --new-version X.Y.Z`

`bump2version` is configured in [`karp-backend/.bumpversion.cfg`](karp-backend/.bumpversion.cfg) and [`karp-lex-core/.bumpversion.cfg`](karp-lex-core/.bumpversion.cfg).

`bump2version` will update version in specific files, commit them and create a tag.

For releasing a new version:
   - `just publish`
   - `make publish`
   - `git push origin main --tags`
