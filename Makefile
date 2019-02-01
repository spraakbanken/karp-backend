default: tox

test:
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests

pytest: build-dev
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests

tox:
	tox

build:
	pipenv install

build-dev:
	pipenv install --dev

flaske8:
	flake8 src tests setup.py wsgi.py

pyre:
	pyre check

run-dev:
	pipenv run python wsgi.py

prepare-release:
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev > requirements-dev.txt

bumpversion-patch: prepare-release
	bumpversion patch

bumpversion-minor: prepare-release
	bumpversion minor

bumpversion-major: prepare-release
	bumpversion major
