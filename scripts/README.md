# Py3plex Scripts

This directory contains utility scripts for the py3plex project.

## lint_docs.py

Documentation linter that checks for common formatting issues and artifacts.

**Usage:**

```bash
# Run from repository root
python scripts/lint_docs.py
```

**What it checks:**

1. **Forbidden patterns:**
   - Encoding/hyphenation artifacts (￾, ˓→, ␣)
   - Page continuation markers ("continued from previous page", "continues on next page")
   - Legacy docker-compose commands (use "docker compose" instead)

2. **Version consistency:**
   - Warns if multiple py3plex version numbers appear in examples
   - Examples should use the current release version

**Exit codes:**

- `0`: All checks passed (or warnings only)
- `1`: Issues found that need fixing

**CI Integration:**

Add to your CI pipeline (e.g., `.github/workflows/docs.yml`):

```yaml
- name: Lint documentation
  run: python scripts/lint_docs.py
```

**Modifying the linter:**

Edit `FORBIDDEN_PATTERNS` in the script to add new checks.
The script scans all `.rst` files in `book/` and `docfiles/` directories.
