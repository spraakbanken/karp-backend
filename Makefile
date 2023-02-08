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
	@echo "usage:"
	@echo ""
	@echo "install"
	@echo "   setup production environment"
	@echo ""
	@echo "dev | install-dev"
	@echo "   setup development environment"
	@echo ""
	@echo "test | run-all-tests"
	@echo "   run all tests"
	@echo ""
	@echo "run-doc-tests"
	@echo "   run all tests"
	@echo ""
	@echo "run-all-tests-w-coverage"
	@echo "   run all tests with coverage collection"
	@echo ""
	@echo "lint"
	@echo "   lint the code"
	@echo ""
	@echo "type-check"
	@echo "   check types"
	@echo ""
	@echo "fmt"
	@echo "   run formatter on all code"

install:
	poetry install --no-dev -E mysql

dev: install-dev
install-dev: components/karp/search/domain/query_dsl/karp_query_v6_parser.py components/karp/search/domain/query_dsl/karp_query_v6_model.py
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

components/karp/search/domain/query_dsl/karp_query_v6_parser.py: grammars/query_v6.ebnf
	${INVENV} tatsu $< > $@

components/karp/search/domain/query_dsl/karp_query_v6_model.py: grammars/query_v6.ebnf
	${INVENV} tatsu --object-model $< > $@

.PHONY: serve
serve: install-dev
	${INVENV} uvicorn --factory karp.karp_v6_api.main:create_app

.PHONY: serve-w-reload
serve-w-reload: install-dev
	${INVENV} uvicorn --reload --factory karp.karp_v6_api.main:create_app

check-security-issues: install-dev
	${INVENV} bandit -r -ll karp

.PHONY: test
test: unit-tests
.PHONY: all-tests
all-tests: unit-tests integration-tests e2e-tests
.PHONY: all-tests-w-coverage
all-tests-w-coverage:
	${INVENV} pytest -vv --cov=karp --cov-report=xml components/karp/tests

.PHONY: unit-tests
unit-tests:
	${INVENV} pytest -vv components/karp/tests/unit bases/karp/lex_core/tests

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

test-log: clean-pyc lint-syntax-errors
	${INVENV} pytest -vv --cov=karp --cov-report=xml karp/tests > pytest.log

tox:
	tox

tox-to-log:
	tox > tox.log

lint:
	${INVENV} pylint --rcfile=pylintrc karp/auth karp/lex karp/cliapp karp/karp_v6_api

lint-no-fail:
	${INVENV} pylint --rcfile=pylintrc --exit-zero karp

check-pylint:
	${INVENV} pylint --rcfile=pylintrc  karp

check-mypy: type-check

.PHONY: serve-docs
serve-docs:
	cd docs/karp-backend-v6 && ${INVENV} mkdocs serve && cd -

.PHONY: lint-refactorings
lint-refactorings: check-pylint-refactorings
check-pylint-refactorings:
	${INVENV} pylint --disable=C,W,E --enable=R karp

.PHONY: type-check
type-check:
	${INVENV} mypy karp

bumpversion:
	${INVENV} bump2version patch

bumpversion-minor:
	${INVENV} bump2version minor

bumpversion-major:
	${INVENV} bump2version major

.PHONY: publish
publish:
	git push origin main --tags

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: fmt
fmt:
	${INVENV} black .
