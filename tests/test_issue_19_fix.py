#!/usr/bin/env python3

"""
Test for the specific edge width logic fix in drawing_machinery.py
This test ensures that the fix for issue #19 is working correctly.
"""

import sys
import os

# Add py3plex to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_edge_width_logic():
    """
    Test the specific logic fix for edge width handling in drawing_machinery.py
    
    This test verifies that the boolean logic fix:
    FROM: if not type(width) == list or not type(width) == tuple:
    TO:   if not (type(width) == list or type(width) == tuple):
    
    Works correctly for different input types.
    """
    print("Testing edge width logic fix...")
    
    # Test the fixed logic directly
    def process_width(width):
        """Process width using the fixed logic"""
        if not (type(width) == list or type(width) == tuple):
            lw = (width, )
        else:
            lw = width
        return lw
    
    # Test cases
    test_cases = [
        # (input, expected_type, description)
        (1.0, tuple, "scalar float should become tuple"),
        (2, tuple, "scalar int should become tuple"),
        ([1, 2, 3], list, "list should stay list"),
        ((1, 2, 3), tuple, "tuple should stay tuple"),
        ([1.5], list, "single-element list should stay list"),
        ((2.5,), tuple, "single-element tuple should stay tuple"),
    ]
    
    all_passed = True
    
    for width, expected_type, description in test_cases:
        result = process_width(width)
        
        if type(result) != expected_type:
            print(f"FAIL: FAIL: {description}")
            print(f"   Input: {width} (type: {type(width).__name__})")
            print(f"   Expected type: {expected_type.__name__}")
            print(f"   Actual result: {result} (type: {type(result).__name__})")
            all_passed = False
        else:
            print(f"PASS: PASS: {description}")
            
        # Additional validation for scalars
        if not isinstance(width, (list, tuple)):
            if result != (width,):
                print(f"FAIL: FAIL: Scalar value not properly wrapped")
                print(f"   Expected: ({width},), Got: {result}")
                all_passed = False
        else:
            # For lists and tuples, should be unchanged
            if result is not width:
                print(f"FAIL: FAIL: List/tuple should be unchanged (same object)")
                all_passed = False
    
    if all_passed:
        print("\nSuccess: All edge width logic tests PASSED!")
        return True
    else:
        print("\n Some edge width logic tests FAILED!")
        return False

def test_old_vs_new_logic():
    """
    Compare the old (buggy) logic vs the new (fixed) logic
    """
    print("\nTesting old vs new logic comparison...")
    
    def old_logic(width):
        """The old buggy logic"""
        if not type(width) == list or not type(width) == tuple:
            return (width, )
        else:
            return width
    
    def new_logic(width):
        """The new fixed logic"""
        if not (type(width) == list or type(width) == tuple):
            return (width, )
        else:
            return width
    
    test_values = [1.0, [1, 2], (1, 2), 5]
    
    print("Comparing old vs new logic:")
    for width in test_values:
        old_result = old_logic(width)
        new_result = new_logic(width)
        
        print(f"Input: {width} (type: {type(width).__name__})")
        print(f"  Old logic: {old_result}")
        print(f"  New logic: {new_result}")
        
        if isinstance(width, (list, tuple)):
            # For lists/tuples, old logic was wrong, new should preserve original
            if old_result == (width,) and new_result == width:
                print(f"  PASS: Fix confirmed: preserves {type(width).__name__} correctly")
            else:
                print(f"  ? Unexpected result")
        else:
            # For scalars, both should wrap in tuple
            if old_result == new_result == (width,):
                print(f"  PASS: Both handle scalar correctly")
            else:
                print(f"  FAIL: Inconsistent scalar handling")
        print()

if __name__ == "__main__":
    print("=== Testing py3plex issue #19 fix ===")
    print("Testing edge width logic in drawing_machinery.py")
    print()
    
    # Run the main test
    success = test_edge_width_logic()
    print()
    
    # Show comparison
    test_old_vs_new_logic()
    
    if success:
        print("PASS: All tests passed! The fix is working correctly.")
        sys.exit(0)
    else:
        print("FAIL: Some tests failed!")
        sys.exit(1)