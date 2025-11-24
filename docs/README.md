# Documentation

This directory contains the PDF version of the py3plex documentation.

## Documentation Sources

- **RST Source Files**: Located in `../docfiles/` directory
- **HTML Documentation**: Available at https://skblaz.github.io/py3plex/ (auto-deployed from RST sources)
- **PDF Documentation**: `py3plex_documentation.pdf` (auto-generated and updated by GitHub Actions)

## Building Documentation

To build the HTML documentation from RST sources:

```bash
cd docfiles
sphinx-build -b html . _build/html
```

Or use the Makefile from the repository root:

```bash
make docs
```

The built HTML is automatically deployed to GitHub Pages via GitHub Actions workflow.

## Note

This directory previously contained static HTML files which caused drift between the source RST files and the published documentation. These have been removed, and only the GitHub Pages site (https://skblaz.github.io/py3plex/) should be used for HTML documentation.
