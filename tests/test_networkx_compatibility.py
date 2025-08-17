#!/usr/bin/env python3
"""
Simple test to verify NetworkX compatibility fixes.
"""

import sys
import os

# Add py3plex to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_networkx_compatibility():
    """Test our NetworkX compatibility layer"""
    print("Testing NetworkX compatibility fixes...")
    
    try:
        # Test basic imports
        from py3plex.core.nx_compat import nx_info, nx_to_scipy_sparse_matrix, is_string_like
        print("✅ NetworkX compatibility imports successful")
        
        # Test with a simple graph
        import networkx as nx
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])
        
        # Test nx_info
        info = nx_info(G)
        print("✅ nx_info working:", info.split('\n')[0])  # Show first line
        
        # Test is_string_like
        assert is_string_like("hello") == True
        assert is_string_like(123) == False
        print("✅ is_string_like working correctly")
        
        # Test basic multinet import
        from py3plex.core import multinet
        print("✅ Basic multinet import successful")
        
        # Test basic visualization import
        from py3plex.visualization.multilayer import draw_multilayer_default
        print("✅ Basic visualization import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ NetworkX compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing py3plex NetworkX compatibility fixes")
    print("=" * 60)
    
    success = test_networkx_compatibility()
    
    if success:
        print("\n🎉 All NetworkX compatibility tests passed!")
        print("✅ The main NetworkX 3.x compatibility issues are resolved")
        sys.exit(0)
    else:
        print("\n❌ NetworkX compatibility tests failed!")
        sys.exit(1)