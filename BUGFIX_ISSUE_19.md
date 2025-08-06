# Fix for Issue #19: Edge Rendering in Multilayer Networks

## Problem Description

The py3plex library had an issue where edges were not being rendered properly in multilayer network visualizations. Users reported that when attempting to visualize multilayer networks using the library's documentation examples, edges within layers were not displayed correctly.

## Root Cause

The issue was traced to a logical error in `py3plex/visualization/drawing_machinery.py` at line 545. The boolean expression:

```python
if not type(width) == list or not type(width) == tuple:
```

This expression always evaluates to `True` because of incorrect boolean logic. Since a variable cannot be both a list AND a tuple simultaneously, either `not type(width) == list` or `not type(width) == tuple` will always be true.

This caused the code to always execute `lw = (width, )`, wrapping all width specifications in tuples, even when users provided lists or tuples of different widths for different edges.

## Fix Applied

The boolean logic was corrected to:

```python
if not (type(width) == list or type(width) == tuple):
```

This ensures that:
- Scalar values (int, float) are wrapped in tuples: `lw = (width, )`
- Lists and tuples are preserved as-is: `lw = width`

## Impact

This fix enables proper multilayer network visualization by:

1. **Preserving multiple edge widths**: When users specify different widths for different edges as lists or tuples, these are now correctly preserved
2. **Maintaining backward compatibility**: Scalar width values continue to work as before
3. **Fixing edge rendering**: Edges in multilayer networks now render properly with their intended widths

## Testing

Two comprehensive test suites were added:

1. `tests/test_issue_19_fix.py`: Tests the specific boolean logic fix
2. `tests/test_multilayer_edge_fix.py`: Tests realistic multilayer network scenarios

Both tests demonstrate the difference between the old (buggy) and new (fixed) behavior.

## Example

Before the fix:
```python
# User specifies different widths for edges
edge_widths = [0.5, 1.0, 1.5]
# Old logic would produce: ([0.5, 1.0, 1.5],) - incorrectly wrapped
# Result: Edges not rendered properly
```

After the fix:
```python
# User specifies different widths for edges  
edge_widths = [0.5, 1.0, 1.5]
# New logic produces: [0.5, 1.0, 1.5] - correctly preserved
# Result: Edges render with proper individual widths
```

This fix resolves the visualization issues described in issue #19 and restores proper multilayer network rendering functionality.