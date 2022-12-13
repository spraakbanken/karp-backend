.PHONY: test-log pytest build-dev clean clean-pyc help lint lint-syntax-errors
.DEFAULT: test

PYTHON = python3
PLATFORM := ${shell uname -o}
# INVENV_PATH = ${shell which invenv}



ifeq (${VIRTUAL_ENV},)
  VENV_NAME = .venv
  INVENV = poetry run
#   ${info invenv: ${INVENV_PATH}}
#   ifeq (${INVENV_PATH},)
#     INVENV = export VIRTUAL_ENV="${VENV_NAME}"; export PATH="${VENV_BIN}:${PATH}"; unset PYTHON_HOME;
#   else
#     INVENV = invenv -C ${VENV_NAME}
#   endif
else
  VENV_NAME = ${VIRTUAL_ENV}
  INVENV =
endif

${info Platform: ${PLATFORM}}
${info Using virtual environment: ${VENV_NAME}}

VENV_BIN = ${VENV_NAME}/bin



ifeq (${PLATFORM}, Android)
  FLAKE8_FLAGS = --jobs=1
else
  FLAKE8_FLAGS = --jobs=auto
endif

help:
	@echo "Available commands:"

install:
	poetry install --no-dev -E mysql

dev: install-dev
install-dev: karp/search/domain/query_dsl/karp_query_v6_parser.py karp/search/domain/query_dsl/karp_query_v6_model.py
	poetry install -E mysql

install-wo-mysql:
	poetry install --no-dev

install-dev-wo-mysql:
	poetry install

install-elasticsearch6:
	poetry install --no-dev -E elasticsearch6

install-dev-elasticsearch6:
	poetry install -E elasticsearch6

install-elasticsearch7:
	poetry install --no-dev -E elasticsearch7

install-dev-elasticsearch7:
	poetry install -E elasticsearch7

init-db:
	${INVENV} alembic upgrade head

karp/search/domain/query_dsl/karp_query_v6_parser.py: grammars/query_v6.ebnf
	${INVENV} tatsu $< > $@

karp/search/domain/query_dsl/karp_query_v6_model.py: grammars/query_v6.ebnf
	${INVENV} tatsu --object-model $< > $@

run: install
	${INVENV} python run.py 8081

.PHONY: serve
serve: install-dev
	${INVENV} uvicorn asgi:app

.PHONY: serve-w-reload
serve-w-reload: install-dev
	${INVENV} uvicorn --reload asgi:app

check-security-issues: install-dev
	${INVENV} bandit -r -ll karp

.PHONY: test
test: unit-tests
.PHONY: all-tests
all-tests: unit-tests integration-tests e2e-tests
.PHONY: all-tests-w-coverage
all-tests-w-coverage:
	${INVENV} pytest -vv --cov=karp --cov-report=xml karp/tests

.PHONY: unit-tests
unit-tests:
	${INVENV} pytest -vv karp/tests/unit karp/tests/foundation/unit

.PHONY: e2e-tests
e2e-tests: clean-pyc
	${INVENV} pytest -vv karp/tests/e2e

.PHONY: run-e2e-tests-w-coverage
e2e-tests-w-coverage: clean-pyc
	${INVENV} pytest -vv --cov=karp --cov-report=xml karp/tests/e2e

.PHONY: integration-tests
integration-tests: clean-pyc
	${INVENV} pytest -vv karp/tests/integration

.PHONY: unit-tests-w-coverage
unit-tests-w-coverage: clean-pyc
	${INVENV} pytest -vv --cov=karp --cov-report=xml karp/tests/unit karp/tests/foundation/unit

.PHONY: integration-tests-w-coverage
integration-tests-w-coverage: clean-pyc
	${INVENV} pytest -vv --cov=karp --cov-report=xml karp/tests/integration

test-log: install-dev clean-pyc lint-syntax-errors
	${INVENV} pytest -vv --cov=karp --cov-report=xml karp/tests > pytest.log

tox:
	tox

tox-to-log:
	tox > tox.log

lint:
	${INVENV} pylint --rcfile=pylintrc karp/auth karp/lex asgi.py karp/cliapp karp/webapp
	# ${INVENV} pylint --rcfile=pylintrc karp asgi.py

lint-no-fail: install-dev
	${INVENV} pylint --rcfile=pylintrc --exit-zero karp asgi.py

check-pylint: install-dev
	${INVENV} pylint --rcfile=pylintrc  karp

check-mypy: type-check

.PHONY: lint-refactorings
lint-refactorings: check-pylint-refactorings
check-pylint-refactorings: install-dev
	${INVENV} pylint --disable=C,W,E --enable=R karp

.PHONY: type-check
type-check:
	${INVENV} mypy karp asgi.py

bumpversion: install-dev
	${INVENV} bump2version patch

bumpversion-minor: install-dev
	${INVENV} bump2version minor

bumpversion-major: install-dev
	${INVENV} bump2version major

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
