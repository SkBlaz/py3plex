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
    
    # 2. Auto-select best algorithm
    result = auto_select_community(
        network,
        fast_mode=True,
        random_state=42
    )
    
    # 3. Print results
    print(f"Best algorithm: {result['best_algorithm']}")
    print(f"Communities: {len(set(result['partition'].values()))}")
    print(f"Score: {result['best_score']:.3f}")
    print("\nLeaderboard:")
    for algo, score in result['leaderboard'][:3]:
        print(f"  {algo}: {score:.3f}")
        
except ImportError:
    print("AutoCommunity requires optional dependencies.")
    print("Install with: pip install py3plex[algos]")
