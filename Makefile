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
