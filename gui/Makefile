# Makefile for building GUI executable

default:
	@echo "NO DEFAULT MAKE TARGET"

# build the GUI app for macos on Intel
app_darwin_x64: dist/experiment dist/yamlwriter
	npm run make-x64

# build the GUI app for macos on ARM
app_darwin_arm64: dist/experiment dist/yamlwriter
	npm run make-arm64

# get the dependencies and devDependencies for the GUI app
deps:
	npm install

# use pyinstaller to build dist/experiment EXE, use specfile
dist/experiment:
	pyinstaller --clean experiment.spec

# use pyinstaller to build dist/yamlwriter EXE, use specfile
dist/yamlwriter:
	pyinstaller --clean yamlwriter.spec

# clean up generated files in dist and out
clean:
	rm -rf dist/*
	rm -rf out/*

