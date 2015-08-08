#
# A GNU Makefile for the project.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

.PHONY: help clean clean-pyc lint tests tests-coverage tests-timings docs

help:
	@echo "clean          - remove build artifacts"
	@echo "clean-pyc      - remove Python file artifacts"
	@echo "lint           - check style with flake8"
	@echo "tests          - run unit tests"
	@echo "tests-coverage - check test code coverage"
	@echo "tests-timings  - obtain test timings"
	@echo "docs           - generate Sphinx HTML documentation, including API docs"

clean: clean-pyc
	@rm -rf .coverage coverage

clean-pyc:
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.py[co]' -exec rm -f {} +

lint:
	@flake8 viewer tests

tests:
	@nosetests tests

tests-coverage:
	@nosetests tests \
		--with-coverage \
		--cover-package viewer \
		--cover-erase \
		--cover-html \
		--cover-html-dir coverage

tests-timings:
	@nosetests tests \
		--with-timer \
		--timer-ok=10ms \
		--timer-warning=50ms

docs:
	@sphinx-apidoc --force -o docs viewer
	@$(MAKE) -C docs clean
	@$(MAKE) -C docs html
