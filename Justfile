default: unit-tests
alias test := unit-tests

PLATFORM := `uname -o`
PROJECT := "sparv_kb_ner"

VENV_NAME := env_var_or_default('VIRTUAL_ENV', '.venv')
INVENV := if env_var_or_default('VIRTUAL_ENV', "") == "" { "poetry run" } else { "" }

info:
	@echo "Platform: {{PLATFORM}}"
	@echo "Venv: {{VENV_NAME}}"
	@echo "INVENV: '{{INVENV}}'"

alias dev := install-dev



# setup production environment
install:
	poetry install --no-dev -E mysql

# setup development environment
install-dev:
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
	{{INVENV}} alembic upgrade head

# build parser
build-parser:
    {{INVENV}} tatsu grammars/query_v6.ebnf > components/karp/search/domain/query_dsl/karp_query_v6_parser.py
    {{INVENV}} tatsu --object-model grammars/query_v6.ebnf > components/karp/search/domain/query_dsl/karp_query_v6_model.py

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
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml components/karp/tests bases/karp/lex_core/tests

# run all tests for karp-lex-core
test-lex-core:
	{{INVENV}} pytest -vv bases/karp/lex_core/tests

# run all tests for karp-lex-core with code coverage
test-lex-core-w-coverage:
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml bases/karp/lex_core/tests

# run unit tests
unit-tests:
    {{INVENV}} pytest -vv components/karp/tests/unit bases/karp/lex_core/tests

# run unit tests with code coverage
unit-tests-w-coverage: clean-pyc
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml components/karp/tests/unit components/karp/tests/foundation/unit

# run given test
run-test TEST:
	{{INVENV}} pytest -vv {{TEST}}

# run end-to-end tests
e2e-tests: clean-pyc
	{{INVENV}} pytest -vv components/karp/tests/e2e

# run end-to-end tests with code coverage
e2e-tests-w-coverage: clean-pyc
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml components/karp/tests/e2e

# run integration tests
integration-tests: clean-pyc
	{{INVENV}} pytest -vv components/karp/tests/integration

# run integration tests with code coverage
integration-tests-w-coverage: clean-pyc
	{{INVENV}} pytest -vv --cov=karp --cov-report=xml components/karp/tests/integration

# lint code
lint:
	{{INVENV}} ruff bases/karp components/karp

# lint specific project
lint-project project:
	@echo "Linting {{project}}"
	cd projects/{{project}} && just lint

serve-docs:
	cd docs/karp-backend-v6 && {{INVENV}} mkdocs serve && cd -


lint-refactorings: check-pylint-refactorings
check-pylint-refactorings:
	{{INVENV}} pylint --disable=C,W,E --enable=R karp

# type-check code
type-check:
	{{INVENV}} mypy -p karp

# type-check code for project
type-check-project project:
	@echo "Type-checking {{project}} ..."
	cd projects/{{project}} && just type-check

# bump patch part of version
bumpversion:
	{{INVENV}} bump2version patch

# bump minor part of version
bumpversion-minor:
	{{INVENV}} bump2version minor

# bump major part of version
bumpversion-major:
	{{INVENV}} bump2version major

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
