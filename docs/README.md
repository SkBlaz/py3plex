# Documentation

This directory contains the py3plex documentation served by GitHub Pages.

## Documentation Files

- **HTML Documentation**: All `.html` files and supporting directories (`_static`, `_images`, `_sources`) - auto-deployed from RST sources
- **PDF Documentation**: `py3plex_documentation.pdf` - auto-generated and updated by GitHub Actions
- **README**: This file

## Documentation Sources

- **RST Source Files**: Located in `../docfiles/` directory
- **Published Documentation**: Available at https://skblaz.github.io/py3plex/

## Building Documentation

To build the HTML documentation from RST sources:

```bash
cd docfiles
sphinx-build -b html . _build/
```

Or use the Makefile from the repository root:

```bash
make docs
```

The built HTML is automatically deployed to this `docs/` folder via GitHub Actions workflow.

## Note

GitHub Pages is configured to serve from this `/docs` folder in the master branch. The documentation is automatically built and deployed by the GitHub Actions workflow on every push to master.
