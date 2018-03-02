.PHONY: dev install publish test

TAG="\n\n\033[0;32m\#\#\# "
END=" \#\#\# \033[0m\n"

all: test

dev:
	@echo $(TAG)Installing dev requirements$(END)
	pip install -r requirements-dev.txt

	@echo $(TAG)Installing stone-burner$(END)
	pip install --editable .

	@echo

install:
	pip install . --upgrade

publish:
	python setup.py sdist upload -r pypi

test: dev
	@echo $(TAG)Running tests on the current Python interpreter with coverage $(END)
	py.test --cov ./stone_burner --cov ./tests --doctest-modules --cov-report term-missing --verbose ./stone_burner ./tests
	@echo
