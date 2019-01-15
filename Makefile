default: tox

test:
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests

pytest: build
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests

tox:
	tox

build:
	pipenv install

flaske8:
	flake8 src tests setup.py wsgi.py

pyre:
	pyre check
