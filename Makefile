.PHONY: help clean clean-pyc lint tests tests-coverage docs

help:
	@echo "clean         - remove build artifacts"
	@echo "clean-pyc     - remove Python file artifacts"
	@echo "lint          - check style with flake8"
	@echo "test          - run unit tests"
	@echo "test-coverage - check test code coverage"
	@echo "docs          - generate Sphinx HTML documentation, including API docs"

clean: clean-pyc
	@rm -rf coverage

clean-pyc:
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.py[co]' -exec rm -f {} +

lint:
	@flake8 viewer tests

test:
	@nosetests tests

test-coverage:
	@nosetests tests --with-coverage \
		--cover-package viewer \
		--cover-erase \
		--cover-html \
		--cover-html-dir coverage

docs:
	@sphinx-apidoc -o docs/ viewer
	@$(MAKE) -C docs clean
	@$(MAKE) -C docs html
