.DEFAULT: test

PLATFORM := ${shell uname -o}


ifeq (${VIRTUAL_ENV},)
  INVENV = poetry run
else
  INVENV =
endif

${info Platform: ${PLATFORM}}


.PHONY: help
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
	poetry install --only=main -E mysql

dev: install-dev
install-dev:
	poetry install -E mysql

# setup CI environment
install-ci: install-dev
	poetry install --only ci

install-wo-mysql:
	poetry install --no-dev

install-dev-wo-mysql:
	poetry install

init-db:
	${INVENV} alembic upgrade head

# build parser
build-parser: karp-backend/src/karp/search/domain/query_dsl/karp_query_v6_parser.py karp-backend/src/karp/search/domain/query_dsl/karp_query_v6_model.py

karp-backend/src/karp/search/domain/query_dsl/karp_query_v6_parser.py: grammars/query_v6.ebnf
	${INVENV} tatsu $< > $@

karp-backend/src/karp/search/domain/query_dsl/karp_query_v6_model.py: grammars/query_v6.ebnf
	${INVENV} tatsu --object-model $< > $@

.PHONY: serve
serve: install-dev
	${INVENV} uvicorn --factory karp.karp_v6_api.main:create_app

.PHONY: serve-w-reload
serve-w-reload: install-dev
	${INVENV} uvicorn --reload --factory karp.karp_v6_api.main:create_app

unit_test_dirs := tests/unit
e2e_test_dirs := tests/e2e
all_test_dirs := tests

default_cov := "--cov=karp-backend/src/karp --cov=karp-lex-core/src/karp"
cov_report := "term-missing"
cov := ${default_cov}

tests := ${unit_test_dirs}
all_tests := ${all_test_dirs}

.PHONY: test
test:
	${INVENV} pytest -vv ${tests}

.PHONY: all-tests
all-tests: clean-pyc unit-tests integration-tests e2e-tests

.PHONY: all-tests-w-coverage
all-tests-w-coverage:
	${INVENV} pytest -vv ${cov} --cov-report=${cov_report} ${all_tests}

.PHONY: test-w-coverage
test-w-coverage:
	${INVENV} pytest -vv ${cov} --cov-report=${cov_report} ${all_tests}
.PHONY: unit-tests
unit-tests:
	${INVENV} pytest -vv ${unit_test_dirs}

.PHONY: e2e-tests
e2e-tests: clean-pyc
	${INVENV} pytest -vv ${e2e_test_dirs}

.PHONY: e2e-tests-w-coverage
e2e-tests-w-coverage: clean-pyc
	${INVENV} pytest -vv ${cov} --cov-report=${cov_report} ${e2e_test_dirs}

.PHONY: integration-tests
integration-tests: clean-pyc
	${INVENV} pytest -vv tests/integration

.PHONY: unit-tests-w-coverage
unit-tests-w-coverage: clean-pyc
	${INVENV} pytest -vv ${cov} --cov-report=${cov_report} ${unit_test_dirs}

.PHONY: integration-tests-w-coverage
integration-tests-w-coverage: clean-pyc
	${INVENV} pytest -vv ${cov} --cov-report=${cov_report} tests/integration

.PHONY: lint
lint:
	${INVENV} ruff ${flags} karp-backend karp-lex-core

.PHONY: build-c4-docs
build-c4-docs:
	structurizr-site-generatr generate-site -w docs/c4-docs/workspace.dsl -o docs/karp-backend/docs/system-overview

.PHONY: serve-docs
serve-docs:
	cd docs/karp-backend && ${INVENV} mkdocs serve && cd -

.PHONY: serve-docs
serve-c4-docs:
	structurizr-site-generatr serve -w docs/c4-docs/workspace.dsl

.PHONY: type-check
type-check:
	${INVENV} mypy --config-file mypy.ini -p karp

.PHONY: publish
publish:
	git push origin main --tags

.PHONY: clean clean-pyc
clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: fmt
fmt:
	${INVENV} black .

# test if code is formatted
.PHONY: check-fmt
check-fmt:
	${INVENV} black . --check

part := "patch"
project := "PLEASE, GIVE ME A PROJECT"

bumpversion:
	cd ${project} && make part=${part} bumpversion

build:
	cd ${project} && make build
