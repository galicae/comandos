format:
	nbqa black nbs/
	nbqa isort nbs/
	nbqa mypy nbs/

export:
	nbdev_export

mypy:
	nbqa mypy nbs/ --ignore-missing-imports --check-untyped-defs

test:
	nbdev_test --n_workers 4

prepare:
	# Export, test, and clean notebooks, and render README if needed
	nbdev_prepare

docs:
	nbdev_docs

all: format prepare mypy
