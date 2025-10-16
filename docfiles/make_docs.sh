#!/bin/bash
# Build Sphinx documentation and copy to docs/ for GitHub Pages
# Note: AUTOGEN_results should not be committed to git (listed in .gitignore)

## Clean the html
rm -rvf html _build;

## Auto-generate the API docs using sphinx-apidoc
echo "Generating API documentation..."
sphinx-apidoc -o AUTOGEN_results -f ../py3plex;

## Generate the HTML documentation
echo "Building HTML documentation..."
make html;

## Copy to the docs folder for GitHub Pages
echo "Copying to docs/ for GitHub Pages..."
cp -rvf _build/html/* ../docs/

## Create .nojekyll file to prevent GitHub Pages from ignoring underscore directories
touch ../docs/.nojekyll

echo "Documentation built successfully!"
echo "Note: AUTOGEN_results/ is auto-generated and should not be committed to git."

