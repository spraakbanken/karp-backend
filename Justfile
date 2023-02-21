default: unit-tests


PLATFORM := `uname -o`

VENV_NAME := env_var_or_default('VIRTUAL_ENV', '.venv')
INVENV := if env_var_or_default('VIRTUAL_ENV', "") == "" { "poetry run" } else { "" }

info:
	@echo "Platform: {{PLATFORM}}"
	@echo "Venv: {{VENV_NAME}}"
	@echo "INVENV: '{{INVENV}}'"

cov-report := "xml"

alias dev := install-dev



# setup production environment
install:
	poetry install --only main -E mysql

# setup development environment
install-dev:
	poetry install -E mysql

install-ci: install-dev
	poetry install --only ci -E mysql

install-wo-mysql:
	poetry install --only main

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
	{{INVENV}} alembic upgrade head

# build parser
build-parser:
    {{INVENV}} tatsu grammars/query_v6.ebnf > karp-backend/src/karp/search/domain/query_dsl/karp_query_v6_parser.py
    {{INVENV}} tatsu --object-model grammars/query_v6.ebnf > karp-backend/src/karp/search/domain/query_dsl/karp_query_v6_model.py

serve: install-dev
	{{INVENV}} uvicorn --factory karp.karp_v6_api.main:create_app


serve-w-reload: install-dev
	{{INVENV}} uvicorn --reload --factory karp.karp_v6_api.main:create_app

check-security-issues: install-dev
	{{INVENV}} bandit -r -ll karp


# run all tests
all-tests: clean-pyc unit-tests integration-tests e2e-tests

# run all tests with code coverage
all-tests-w-coverage:
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml karp-backend/src/karp/tests karp-lex-core/src/karp/lex_core/tests

# run all tests for karp-lex-core
test-lex-core: (test 'karp-lex-core/src/karp/lex_core/tests')

# run all tests for karp-lex-core with code coverage
test-lex-core-w-coverage: (test-w-coverage "--cov=karp.lex_core" "karp-lex-core/src/karp/lex_core/tests")

# run unit tests
unit-tests: test

# run unit tests with code coverage
unit-tests-w-coverage: clean-pyc
	{{INVENV}} pytest -vv --cov=karp --cov-report={{cov-report}} karp-backend/src/karp/tests/unit karp-backend/src/karp/tests/foundation/unit

all-test-dirs := "karp-backend/src/karp/tests karp-lex-core/src/karp/lex_core/tests"
default-cov := "--cov=karp-backend/src/karp --cov=karp-lex-core/src/karp"

# run tests with code coverage
test-w-coverage cov=default-cov +tests=all-test-dirs: clean-pyc
	{{INVENV}} pytest -vv {{cov}} --cov-report={{cov-report}} {{tests}}

unit-test-dirs := "karp-backend/src/karp/tests/unit karp-lex-core/src/karp/lex_core/tests"

# run given test(s)
test *tests=unit-test-dirs:
	{{INVENV}} pytest -vv {{tests}}

# run end-to-end tests
e2e-tests: clean-pyc (test "karp-backend/src/karp/tests/e2e")

# run end-to-end tests with code coverage
e2e-tests-w-coverage: clean-pyc
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml karp-backend/src/karp/tests/e2e

# run integration tests
integration-tests: clean-pyc (test "karp-backend/src/karp/tests/integration")

# run integration tests with code coverage
integration-tests-w-coverage: clean-pyc (test-w-coverage default-cov "karp-backend/src/karp/tests/integration")

# lint code
lint flags="":
	{{INVENV}} ruff {{flags}} karp-backend karp-lex-core

# lint specific project
lint-project project:
	@echo "Linting {{project}}"
	cd projects/{{project}} && just lint

serve-docs:
	cd docs/karp-backend-v6 && {{INVENV}} mkdocs serve && cd -

# type-check code
type-check:
	{{INVENV}} mypy -p karp

# type-check code for project
type-check-project project:
	@echo "Type-checking {{project}} ..."
	cd projects/{{project}} && just type-check

# bump given part of version
bumpversion project part="patch":
	cd {{project}} && just bumpversion {{part}}

# bump minor part of version
bumpversion-minor project: (bumpversion project "minor")

# bump major part of version
bumpversion-major project: (bumpversion project "major")

# push tags to github, where a workflow upload distrivbutionto PyPi
publish:
	git push origin main --tags

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# run formatter
fmt:
	{{INVENV}} black .

# test if code is formatted
check-fmt:
	{{INVENV}} black . --check

# build given project
build-project project:
	@echo "Building {{project}} ..."
	cd projects/{{project}} && just build
