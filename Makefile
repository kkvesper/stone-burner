.PHONY: install

install:
	pip install . --upgrade

publish:
	python setup.py sdist upload -r pypi
