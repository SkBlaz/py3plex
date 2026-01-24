# Documentation Examples

This directory contains executable examples that are:
1. **Runnable** - Each example is a standalone Python script
2. **Tested** - CI automatically runs and validates every example
3. **Documented** - Outputs are embedded in RST documentation

## Structure

Each example:
- Is a single `.py` file
- Includes docstring describing what it demonstrates
- Produces deterministic output
- Is tested in CI

## Adding New Examples

1. Create `example_name.py` in this directory
2. Add docstring with clear description
3. Ensure output is deterministic
4. Run `scripts/generate_docs_outputs.py` to capture output
5. Reference in RST files using `.. literalinclude::` and `.. include::`

## Output Management

- Example outputs are captured in `docs_outputs/`
- Outputs are automatically embedded in RST files
- CI validates that RST outputs match captured outputs

## Conventions

- Keep examples focused and minimal
- Use descriptive variable names
- Include comments for clarity
- Print results in a clear, consistent format
