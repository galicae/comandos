format:
	nbqa black nbs/
	nbqa isort nbs/

export:
	nbdev-export

test:
	nbdev-test --n_workers 4

prepare:
	# Export, test, and clean notebooks, and render README if needed
	nbdev-prepare

docs:
	nbdev-docs

release:
	git push
	nbdev-release-git
	nbdev-pypi
	anaconda login
	nbdev-conda
	nbdev-bump-version

all: format prepare 
