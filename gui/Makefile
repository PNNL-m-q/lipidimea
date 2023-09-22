# Makefile for building GUI executable

# default rule, list all of the defined rules
.PHONY: list
list:
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

# build the GUI app for macos on Intel
app_darwin_x64: dist/experiment dist/yamlwriter docs version
	@echo "-> building GUI app for MacOS (Intel)"
	@npm run make-x64

# build the GUI app for macos on ARM
app_darwin_arm64: dist/experiment dist/yamlwriter docs version
	@echo "-> building GUI app for MacOS (ARM)"
	@npm run make-arm64

# get the dependencies and devDependencies for the GUI app
deps:
	@echo "-> installing app dependencies with npm"
	@npm install

# use pyinstaller to build dist/experiment EXE, use specfile
dist/experiment:
	@echo "-> building experiment EXE with pyinstaller"
	@pyinstaller --clean experiment.spec

# use pyinstaller to build dist/yamlwriter EXE, use specfile
dist/yamlwriter:
	@echo "-> building yamlwriter EXE with pyinstaller"
	@pyinstaller --clean yamlwriter.spec

# go into docs and build the HTML documentation
# then copy that into gui/src/docs/
docs:
	@echo "-> building HTML docs"
	@cd ../docs && make html
	@echo "-> copying HTML docs to gui/src/docs/"
	@cp -r ../docs/build/html/* src/docs/

# grab the current version from the Python package and update package.json
version:
	@echo "-> updating GUI version from LipidIMEA Python package"
	@python3 update_version.py

# clean up generated files in dist and out
clean:
	@echo "-> removing everything under dist/ and out/"
	@rm -rf dist/*
	@rm -rf out/*

