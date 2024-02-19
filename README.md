<!-- @format -->

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

A Makefile is provided to simplify tasks.

### Getting started

1. First clone this repo: `git clone` or `gh repo clone` (if using github-cli).

2. Install dependencies:

  `make dev` (or `make install-dev`)

3. Install MariaDB and create a database

4. Setup environment variables (can be placed in a `.env` file in the root and then **?** `poetry run` sets those):
   ```
   export DB_DATABASE=<name of database>
   export DB_USER=<database user>
   export DB_PASSWORD=<user's password>
   export DB_HOST=localhost
   export AUTH_JWT_PUBKEY_PATH=/path/to/pubkey
   ```
5. Activate the virtual environment by running: `poetry shell`
6. Run `karp-cli db up` to initialize database
7. Run `make serve` or `make serve-w-reload` to start development server

   or `poetry shell` and then `uvicorn --factory karp.karp_v6_api.main:create_app`

8. To setup Elasticsearch, download Elasticsearch 8.x and run the
   following commands from the `elasticsearch-8.XXX` directory:
   ```
   bin/elasticsearch-plugin install analysis-phonetic
   bin/elasticsearch-plugin install analysis-icu
   ```
   Then edit the file `config/elasticsearch.yml`, find the line:
   ```
   xpack.security.enabled = true
   ```
   and change `true` to `false`.
   Then run `bin/elasticsearch` to start it.
9. Add environment variables

```
export ES_ENABLED=true
export ELASTICSEARCH_HOST=http://localhost:9200
```

## Create test resources

1. `poetry shell` and then:
2. `karp-cli resource create assets/testing/config/places.json`
3. `karp-cli entries add places assets/testing/data/places.jsonl`
4. Do the same for `municipalities`
5. `karp-cli resource publish places 1`
6. `karp-cli resource publish municipalities 1`

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

### Testing

The tests are organized in unit, integration and end-to-end tests.

#### Unit tests

These test should have no infrastructure dependencies and should run fast.

Run them by:

- From repo root:
  - `make test` (or `make unit-tests`)
  - `make unit-tests-w-coverage` or `make cov-report=xml unit-tests-w-coverage`
  - `make test-w-coverage tests/unit`
  - `make unit-tests-w-coverage` or `make cov_report=xml unit-tests-w-coverage`
  - `make all_tests="tests/unit" test-w-coverage`

#### Integration tests

These test have some infrastructure dependencies and should run slower.

Run them by:

- From repo root:
  - `make integration-tests`
  - `make integration-tests-w-coverage` or `make cov-report=xml integration-tests-w-coverage`
  - `make test-w-coverage tests/integration`
  - `make integration-tests-w-coverage` or `make cov_report=xml integration-tests-w-coverage`
  - `make all_tests=tests/integration test-w-coverage`

#### End-to-end tests

These test have all infrastructure dependencies and should run slowest.

Run them by:

- From repo root:
  - `make e2e-tests`
  - `make e2e-tests-w-coverage` or `make cov-report=xml e2e-tests-w-coverage`
  - `make test-w-coverage tests/e2e`
  - `make e2e-tests-w-coverage` or `make cov_report=xml e2e-tests-w-coverage`
  - `make all_tests=tests/e2e test-w-coverage`

#### All tests

These test have all infrastructure dependencies and should run slowest.

Run them by:

- From repo root:
  - `make all-tests`
  - `make test-w-coverage` or `make cov-report=xml test-w-coverage`
  - `make all-tests-w-coverage`
  - `make test-w-coverage` or `make cov_report=xml test-w-coverage`
  - `make all-tests-w-coverage`

### Linting

Linting is done by [`ruff`](https://beta.ruff.rs/docs/).

Run with `make lint`. Settings are in `ruff.toml`.

Usual commands for `ruff` is:

- `ruff --fix <path>` tries to fix linting problems.
- `ruff --add-noqa <path>` add noqa:s (silence lint) to each line that needs

### Formatting

Formatting is done by `black`.

Run formatter with `make fmt`, check if formatting is needed `make check-fmt`.

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

### Version handling

Version can be bumped with [`bump2version`](https://pypi.org/project/bump2version/).

Usage for:

- Increase patch number `a.b.X => a.b.(X+1)`:
  - From repo root for project `<project>`
    - `make project=<project> bumpversion`
  - From project root
    - `make bumpversion`
    - `bump2version patch`
- Increase minor number `a.X.c => a.(X+1).0`:
  - From repo root for project `<project>`
    - `make project=<project> part=minor bumpversion`
  - From project root
    - `make part=minor bumpversion`
    - `bump2version minor`
- Increase major number `X.b.c => (X+1).0.0`:
  - From repo root for project `<project>`
    - `make project=<project> part=major bumpversion`
  - From project root
    - `make part=major bumpversion`
    - `bump2version major`
- To custom version `a.b.c => X.Y.Z`:
  - From repo root for project `<project>`
    - `make project=<project> part="--new-version X.Y.Z" bumpversion`
  - From project root
    - `make part="--new-version X.Y.Z" bumpversion`
    - `bumpversion --new-version X.Y.Z`

`bump2version` is configured in [`karp-backend/.bumpversion.cfg`](karp-backend/.bumpversion.cfg) and [`karp-lex-core/.bumpversion.cfg`](karp-lex-core/.bumpversion.cfg).

`bump2version` will update version in specific files, commit them and create a tag.

For releasing a new version:

- `make publish`
- `git push origin main --tags`
