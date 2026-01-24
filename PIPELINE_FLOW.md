# Examples-as-Tests-as-Docs Pipeline Flow

## Overview

This document shows the complete flow of the Examples-as-Tests-as-Docs pipeline.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPER WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. Write Example
   ↓
   examples/docs/03_new_example.py
   ↓
2. Run Generator
   ↓
   $ python scripts/generate_docs_outputs.py
   ↓
3. Output Captured
   ↓
   examples/docs_outputs/03_new_example.txt
   examples/docs_outputs/manifest.json (updated)
   ↓
4. Reference in RST
   ↓
   docfiles/my_doc.rst:
   .. literalinclude:: ../examples/docs_outputs/03_new_example.txt
   ↓
5. Validate
   ↓
   $ python scripts/validate_docs_outputs.py
   ↓
6. Commit
   ↓
   $ git add examples/docs/ examples/docs_outputs/
   $ git commit -m "Add example: new_example"
   ↓
7. Push
   ↓
   $ git push

┌─────────────────────────────────────────────────────────────────┐
│                      CI WORKFLOW                                 │
└─────────────────────────────────────────────────────────────────┘

Push/PR Trigger
   ↓
GitHub Actions: docs-examples.yml
   ↓
1. Checkout code
   ↓
2. Setup Python
   ↓
3. Run all examples
   ↓
   $ python scripts/generate_docs_outputs.py
   ↓
   For each example in examples/docs/:
   - Run example
   - Capture stdout/stderr
   - Save to docs_outputs/
   ↓
4. Compare outputs
   ↓
   $ git diff --exit-code examples/docs_outputs/
   ↓
   If differences found:
   ├─→ FAIL ❌ (outputs diverged)
   │   └─→ Upload artifacts
   │       └─→ Block merge
   │
   └─→ SUCCESS ✓ (outputs match)
       └─→ Continue
   ↓
5. Validate RST references
   ↓
   $ python scripts/validate_docs_outputs.py
   ↓
   For each RST file:
   - Find literalinclude directives
   - Verify referenced files exist
   - Check they're in manifest
   ↓
   If validation fails:
   ├─→ FAIL ❌ (missing references)
   │   └─→ Block merge
   │
   └─→ SUCCESS ✓ (all valid)
       └─→ Allow merge

┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION BUILD                           │
└─────────────────────────────────────────────────────────────────┘

Sphinx Build
   ↓
Process RST files
   ↓
Find literalinclude directives
   ↓
Include content from:
   examples/docs_outputs/*.txt
   ↓
Rendered Documentation
   ↓
   [Exact output from CI-run examples]
```

## Component Interaction

```
┌──────────────────┐
│ examples/docs/   │ ← Developer writes examples
│ *.py            │
└────────┬─────────┘
         │
         │ reads
         ↓
┌────────────────────────┐
│ generate_docs_outputs  │ ← Runs examples, captures outputs
│ .py                    │
└────────┬───────────────┘
         │
         │ writes
         ↓
┌──────────────────────────┐
│ examples/docs_outputs/   │ ← Stores captured outputs
│ *.txt + manifest.json    │
└────────┬─────────────────┘
         │
         ├─────────────────┐
         │                 │
         │ reads           │ validates
         ↓                 ↓
┌────────────────┐  ┌──────────────────────┐
│ docfiles/      │  │ validate_docs_outputs│
│ *.rst          │  │ .py                  │
│                │  └──────────┬───────────┘
│ literalinclude │             │
└────────────────┘             │ checks
                               ↓
                        ┌─────────────┐
                        │ CI Workflow │
                        │ Pass/Fail   │
                        └─────────────┘
```

## Data Flow

```
Example Script (*.py)
   ↓
   [Execute in clean environment]
   ↓
stdout + stderr
   ↓
   [Capture and clean]
   ↓
Output File (*.txt)
   ↓
   [Store with metadata]
   ↓
Manifest (manifest.json)
   {
     "examples": {
       "filename.py": {
         "output": "filename.txt",
         "timestamp": "...",
         "size": 1234
       }
     }
   }
   ↓
RST File (*.rst)
   .. literalinclude:: ../examples/docs_outputs/filename.txt
   ↓
   [Sphinx processes]
   ↓
Rendered HTML
   [Exact output from example]
```

## Success Path

```
✓ Write example
   ↓
✓ Generate outputs
   ↓
✓ Outputs committed
   ↓
✓ Reference in RST
   ↓
✓ Push to GitHub
   ↓
✓ CI runs examples
   ↓
✓ Outputs match
   ↓
✓ Validation passes
   ↓
✓ Merge allowed
   ↓
✓ Docs always accurate
```

## Failure Path

```
✗ Write example
   ↓
✗ Generate outputs
   ↓
✗ Forget to commit outputs
   ↓
✗ Push to GitHub
   ↓
✗ CI runs examples
   ↓
✗ Outputs differ
   ↓
✗ CI FAILS ❌
   ↓
✗ Merge blocked
   ↓
→ Fix: Run generator locally
   ↓
→ Commit outputs
   ↓
→ Push again
   ↓
✓ CI passes
```

## Key Guarantees

1. **1:1 Mapping**: Each `.py` → exactly one `.txt` → referenced in RST
2. **CI Execution**: Every example runs in CI on every push/PR
3. **Auto-Capture**: All outputs are generated, never hand-written
4. **Divergence Detection**: CI compares generated vs committed outputs
5. **Validation**: All RST references are checked for correctness

## Benefits

- ✅ **Always Accurate**: Docs show actual current behavior
- ✅ **No Drift**: CI catches when docs are out of date
- ✅ **Testable**: Examples are executable tests
- ✅ **Maintainable**: One command regenerates all outputs
- ✅ **Transparent**: Anyone can verify outputs locally

## Summary

The pipeline ensures that documentation examples are:
1. **Runnable** - They're real Python scripts
2. **Tested** - CI executes them on every change
3. **Accurate** - Outputs are captured, not hand-written
4. **Validated** - CI enforces consistency
5. **Maintainable** - Easy to update and extend
