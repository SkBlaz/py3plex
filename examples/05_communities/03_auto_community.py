"""
Communities: AutoCommunity (flagship feature).

Demonstrates:
- Automatic algorithm selection
- Multi-metric evaluation
- Result explanation

Note: Requires optional dependencies. Install with: pip install py3plex[algos]
"""

try:
    from py3plex.algorithms.community_detection import auto_select_community
    from py3plex.datasets import load_aarhus_cs
    
    # 1. Load network
    network = load_aarhus_cs()
    
    # 2. Auto-select best algorithm (with time limit for CI)
    result = auto_select_community(
        network,
        fast=True,
        max_candidates=3,
        time_budget_s=2.0,
        seed=42
    )
    
    # 3. Print results
    print(f"Best algorithm: {result.algorithm['name']}")
    print(f"Communities: {len(set(result.partition.values()))}")
    print(f"\nTop 3 from leaderboard:")
    print(result.leaderboard.head(3))
        
except ImportError:
    print("AutoCommunity requires optional dependencies.")
    print("Install with: pip install py3plex[algos]")
