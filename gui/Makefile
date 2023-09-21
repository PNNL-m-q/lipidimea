# Makefile for building GUI executable

# build the GUI app for macos on Intel
app_darwin_x64: dist/experiment dist/yamlwriter
	npm run make-x64

# get the devDependencies for the GUI app
deps:
	npm install

# use pyinstaller to build dist/experiment EXE, use specfile
dist/experiment:
	pyinstaller experiment.spec

# use pyinstaller to build dist/yamlwriter EXE, no need for specfile
dist/yamlwriter:
	pyinstaller src/experiment/yamlwriter.py

# clean up generated files in dist and out
clean:
	rm -rf dist/*
	rm -rf out/*

