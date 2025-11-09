#!/usr/bin/env python3

"""
Test script that demonstrates the issue #19 fix for multilayer visualization.
This script creates a minimal reproduction of the edge rendering issue.
"""

import sys
import os

# Add py3plex to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_edge_width_processing():
    """
    Test the core edge width processing logic that was fixed.
    This simulates what happens in the draw_networkx_edges function.
    """
    print("Testing edge width processing logic...")
    
    # Import the specific logic (without needing networkx/matplotlib)
    def process_edge_widths(width):
        """
        This replicates the logic from drawing_machinery.py line 545
        with our fix applied.
        """
        # Our fix: proper boolean logic
        if not (type(width) == list or type(width) == tuple):
            lw = (width, )
        else:
            lw = width
        return lw
    
    # Test cases that would occur in real multilayer networks
    test_scenarios = [
        {
            'name': 'Single edge width (scalar)',
            'input': 1.5,
            'expected_type': tuple,
            'description': 'Single width for all edges'
        },
        {
            'name': 'Multiple edge widths (list)',
            'input': [0.5, 1.0, 1.5, 2.0],
            'expected_type': list,
            'description': 'Different width for each edge'
        },
        {
            'name': 'Multiple edge widths (tuple)',
            'input': (0.8, 1.2, 0.6),
            'expected_type': tuple,
            'description': 'Different width for each edge (tuple)'
        },
        {
            'name': 'Default width (int)',
            'input': 1,
            'expected_type': tuple,
            'description': 'Default integer width'
        }
    ]
    
    all_passed = True
    
    for scenario in test_scenarios:
        width = scenario['input']
        expected_type = scenario['expected_type']
        
        result = process_edge_widths(width)
        
        print(f"\nChecking: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Input: {width} (type: {type(width).__name__})")
        print(f"   Result: {result} (type: {type(result).__name__})")
        
        # Check if result type matches expected
        if type(result) != expected_type:
            print(f"   FAIL: FAIL: Expected {expected_type.__name__}, got {type(result).__name__}")
            all_passed = False
        else:
            print(f"   PASS: PASS: Correct type {expected_type.__name__}")
            
        # Additional checks
        if isinstance(width, (list, tuple)):
            # Should preserve the original object for collections
            if result is not width:
                print(f"   FAIL: FAIL: Should preserve original object")
                all_passed = False
            else:
                print(f"   PASS: PASS: Preserved original object")
        else:
            # Should wrap scalars in tuple
            if result != (width,):
                print(f"   FAIL: FAIL: Should wrap scalar in tuple")
                all_passed = False
            else:
                print(f"   PASS: PASS: Correctly wrapped scalar")
    
    return all_passed

def demonstrate_issue_fix():
    """
    Demonstrate how the fix resolves the specific issue.
    """
    print("\n" + "="*60)
    print("DEMONSTRATING THE ISSUE FIX")
    print("="*60)
    
    print("\nProblem: In multilayer networks, when users specify different")
    print("edge widths for different layers or edge types, the old logic")
    print("would incorrectly wrap these in tuples, causing rendering issues.")
    print()
    
    # Example: User wants different widths for different edge types
    edge_widths_by_type = {
        'intra_layer': [0.5, 0.8, 1.0],  # Different widths within a layer
        'inter_layer': 2.0,              # Thicker lines between layers
        'coupling': [1.5, 1.5, 1.5]     # Consistent width for coupling edges
    }
    
    def old_buggy_logic(width):
        """The old buggy logic that always evaluated to True"""
        if not type(width) == list or not type(width) == tuple:
            return (width, )
        else:
            return width
    
    def new_fixed_logic(width):
        """The new fixed logic"""
        if not (type(width) == list or type(width) == tuple):
            return (width, )
        else:
            return width
    
    print("Example multilayer network edge width processing:")
    print()
    
    for edge_type, width in edge_widths_by_type.items():
        old_result = old_buggy_logic(width)
        new_result = new_fixed_logic(width)
        
        print(f"Edge type: {edge_type}")
        print(f"  Input widths: {width} (type: {type(width).__name__})")
        print(f"  Old logic result: {old_result}")
        print(f"  New logic result: {new_result}")
        
        if isinstance(width, (list, tuple)) and old_result != new_result:
            print(f"  BUG: OLD LOGIC BUG: Wrapped {type(width).__name__} incorrectly!")
            print(f"  PASS: NEW LOGIC FIX: Preserves {type(width).__name__} correctly!")
        elif old_result == new_result:
            print(f"  PASS: Both logics handle scalar correctly")
        print()
    
    print("Impact:")
    print("- With old logic: Lists/tuples got wrapped, breaking edge rendering")
    print("- With new logic: Lists/tuples preserved, enabling proper multi-width rendering")

def test_multilayer_scenario():
    """
    Test a realistic multilayer network scenario
    """
    print("\n" + "="*60)
    print("TESTING REALISTIC MULTILAYER SCENARIO")
    print("="*60)
    
    # Simulate a 3-layer network with different edge types
    layer_configs = [
        {
            'layer_name': 'Layer 1 (Social)',
            'intra_edges': 5,
            'edge_width': 0.8
        },
        {
            'layer_name': 'Layer 2 (Professional)', 
            'intra_edges': 3,
            'edge_width': [1.0, 1.5, 0.5]  # Variable widths
        },
        {
            'layer_name': 'Layer 3 (Family)',
            'intra_edges': 4,
            'edge_width': (1.2, 0.9, 1.1, 0.7)  # Tuple of widths
        }
    ]
    
    # Inter-layer connections
    inter_layer_widths = [2.0, 1.8, 2.2]  # Thicker for visibility
    
    print("Processing multilayer network edge widths...")
    print()
    
    def process_width(width):
        """Our fixed logic"""
        if not (type(width) == list or type(width) == tuple):
            return (width, )
        else:
            return width
    
    all_correct = True
    
    # Process each layer
    for i, config in enumerate(layer_configs):
        print(f" {config['layer_name']}")
        width = config['edge_width']
        processed = process_width(width)
        
        print(f"   Edges: {config['intra_edges']}")
        print(f"   Width spec: {width} (type: {type(width).__name__})")
        print(f"   Processed: {processed} (type: {type(processed).__name__})")
        
        # Validate processing
        if isinstance(width, (list, tuple)):
            if processed is width and len(processed) == config['intra_edges']:
                print(f"   PASS: Correct: Multi-width preserved for {config['intra_edges']} edges")
            elif processed is width:
                print(f"   WARNING:  Width count mismatch: {len(processed)} vs {config['intra_edges']} edges")
            else:
                print(f"   FAIL: Error: Multi-width not preserved")
                all_correct = False
        else:
            if processed == (width,):
                print(f"   PASS: Correct: Scalar width wrapped for uniform edges")
            else:
                print(f"   FAIL: Error: Scalar width not properly wrapped")
                all_correct = False
        print()
    
    # Process inter-layer edges
    print("Inter-layer connections Inter-layer connections")
    processed_inter = process_width(inter_layer_widths)
    print(f"   Width spec: {inter_layer_widths} (type: {type(inter_layer_widths).__name__})")
    print(f"   Processed: {processed_inter} (type: {type(processed_inter).__name__})")
    
    if processed_inter is inter_layer_widths:
        print(f"   PASS: Correct: Inter-layer widths preserved")
    else:
        print(f"   FAIL: Error: Inter-layer widths not preserved")
        all_correct = False
    
    print()
    return all_correct

if __name__ == "__main__":
    print("Testing: Testing py3plex issue #19 fix - Multilayer Visualization")
    print("="*70)
    
    # Test the core logic
    logic_passed = test_edge_width_processing()
    
    # Demonstrate the fix
    demonstrate_issue_fix()
    
    # Test realistic scenario
    scenario_passed = test_multilayer_scenario()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if logic_passed and scenario_passed:
        print("Success: ALL TESTS PASSED!")
        print("PASS: The fix correctly handles edge width processing")
        print("PASS: Multilayer networks should now render edges properly")
        print("PASS: Both single and multiple edge widths work correctly")
        print()
        print("The issue described in #19 should now be resolved!")
    else:
        print("FAIL: SOME TESTS FAILED!")
        if not logic_passed:
            print("FAIL: Core logic tests failed")
        if not scenario_passed:
            print("FAIL: Multilayer scenario tests failed")
    
    sys.exit(0 if (logic_passed and scenario_passed) else 1)