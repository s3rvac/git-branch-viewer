#
# A GNU Makefile for the project.
#
# Copyright: (c) 2014 by Petr Zemek <s3rvac@gmail.com> and contributors
# License: BSD, see LICENSE for more details
#

.PHONY: help clean clean-pyc docs lint tests tests-coverage tests-timings

help:
	@echo "Use \`make <target>', where <target> is one of the following:"
	@echo "  clean          - remove all generated files"
	@echo "  clean-pyc      - remove just Python file artifacts"
	@echo "  docs           - generate documentation"
	@echo "  lint           - check code style with flake8"
	@echo "  tests          - run tests"
	@echo "  tests-coverage - check test coverage"
	@echo "  tests-timings  - obtain test timings"

clean: clean-pyc
	@rm -rf .coverage coverage

clean-pyc:
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.py[co]' -exec rm -f {} +

docs:
	@sphinx-apidoc --force -o docs viewer
	@$(MAKE) -C docs clean
	@$(MAKE) -C docs html

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
