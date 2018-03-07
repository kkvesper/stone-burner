.PHONY: test dev install publish lint

TAG="\n\n\033[0;32m\#\#\# "
END=" \#\#\# \033[0m\n"

test: dev
	@echo $(TAG)Running tests on the current Python interpreter with coverage$(END)
	py.test --cov ./stone_burner --cov ./tests --doctest-modules --cov-report term-missing --verbose ./stone_burner ./tests

	@echo

dev:
	@echo $(TAG)Installing dev requirements$(END)
	pip install -r requirements-dev.txt

	@echo $(TAG)Installing stone-burner in editable mode$(END)
	pip install --editable .

	@echo

install:
	@echo $(TAG)Installing stone-burner$(END)
	pip install . --upgrade

	@echo

publish: test
	@echo $(TAG)Publishing package to pypi$(END)
	python setup.py sdist upload -r pypi

	@echo

lint: dev
	@echo $(TAG)Running pylint$(END)
	pylint stone_burner -f colorized

	@echo
