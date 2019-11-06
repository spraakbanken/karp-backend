.PHONY: test test-to-log pytest build-dev run-tests clean clean-pyc
.DEFAULT: test

run-tests: lint type-check test

test: build-dev clean-pyc
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests

test-queryapi: build-dev clean-pyc
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests/test_query_api.py

test-to-log: build-dev clean-pyc
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests > pytest.log

tox:
	tox

tox-to-log:
	tox > tox.log

build: .venv-build
.venv-build: Pipfile
	pipenv install
	touch $@

build-dev: .venv-build-dev
.venv-build-dev: Pipfile
	pipenv install --dev
	touch $@

lint:
	flake8 src tests setup.py wsgi.py

type-check:
	pyre check

run-dev: build-dev
	pipenv run python wsgi.py

prepare-release:
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev > requirements-dev.txt

docs/openapi.html: doc/karp_api_spec.yaml
	@echo "Skipping 'redoc-cli bundle --output $@ $<'"
	touch $@

bumpversion-patch:
	bumpversion patch

bumpversion-minor:
	bumpversion minor

bumpversion-major:
	bumpversion major

mkrelease-patch: bumpversion-patch prepare-release docs/openapi.html
mkrelease-minor: bumpversion-minor prepare-release docs/openapi.html
mkrelease-major: bumpversion-major prepare-release docs/openapi.html

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm {} \;
	find . -type d -name '__pycache__' -exec rm -rf {} \;
	rm -rf .pytest_cache
