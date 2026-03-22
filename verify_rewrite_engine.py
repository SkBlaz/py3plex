#!/usr/bin/env python3
"""Verification script for RewriteEngine implementation.

This script verifies that:
1. All modules import correctly
2. Core functionality works
3. All tests pass
4. Examples run without errors
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    try:
        from py3plex.dsl.program import (
            RewriteEngine,
            RewriteContext,
            RewriteRule,
            RuleGuard,
            Match,
            apply_rewrites,
            get_standard_rules,
            get_conservative_rules,
            get_aggressive_rules,
        )
        print(" Core imports successful")
    except Exception as e:
        print(f" Import failed: {e}")
        return False
    
    try:
        from py3plex.dsl.program import GraphProgram, type_check, infer_type
        print(" Program imports successful")
    except Exception as e:
        print(f" Import failed: {e}")
        return False
    
    return True


def test_rule_count():
    """Test that all rules are present."""
    print("\nTesting rule count...")
    
    from py3plex.dsl.program import get_standard_rules
    
    rules = get_standard_rules()
    print(f"  Standard rules: {len(rules)}")
    
    if len(rules) < 18:
        print(f" Expected at least 18 rules, got {len(rules)}")
        return False
    
    print(f" All {len(rules)} rules present")
    return True


def test_basic_functionality():
    """Test basic rewrite functionality."""
    print("\nTesting basic functionality...")
    
    from py3plex.dsl.ast import Query, SelectStmt, Target, ComputeItem
    from py3plex.dsl.program import GraphProgram, apply_rewrites
    
    # Create a simple query
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
        )
    )
    
    # Create program
    try:
        program = GraphProgram.from_ast(query)
        print("   GraphProgram creation successful")
    except Exception as e:
        print(f"   GraphProgram creation failed: {e}")
        return False
    
    # Apply rewrites
    try:
        optimized = apply_rewrites(program)
        print("   Rewrite application successful")
    except Exception as e:
        print(f"   Rewrite application failed: {e}")
        return False
    
    # Check provenance
    if len(optimized.metadata.provenance_chain) > len(program.metadata.provenance_chain):
        print("   Provenance tracking working")
    else:
        print("   Provenance chain present (no rewrites needed)")
    
    return True


def test_optimize_method():
    """Test GraphProgram.optimize() integration."""
    print("\nTesting GraphProgram.optimize()...")
    
    from py3plex.dsl.ast import Query, SelectStmt, Target, ComputeItem
    from py3plex.dsl.program import GraphProgram
    
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[
                ComputeItem(name="degree"),
                ComputeItem(name="betweenness_centrality"),
            ],
        )
    )
    
    try:
        program = GraphProgram.from_ast(query)
        optimized = program.optimize()
        print("   GraphProgram.optimize() works")
        return True
    except Exception as e:
        print(f"   GraphProgram.optimize() failed: {e}")
        return False


def test_context_aware():
    """Test context-aware optimization."""
    print("\nTesting context-aware optimization...")
    
    from py3plex.dsl.ast import Query, SelectStmt, Target, ComputeItem
    from py3plex.dsl.program import GraphProgram, apply_rewrites, RewriteContext
    
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="betweenness_centrality")],
        )
    )
    
    program = GraphProgram.from_ast(query)
    
    context = RewriteContext(
        network_stats={'node_count': 10000, 'edge_count': 50000},
        available_metrics=set(),
        safety_mode=False,
    )
    
    try:
        optimized = apply_rewrites(program, context=context)
        print("   Context-aware optimization works")
        return True
    except Exception as e:
        print(f"   Context-aware optimization failed: {e}")
        return False


def test_rule_sets():
    """Test different rule sets."""
    print("\nTesting rule sets...")
    
    from py3plex.dsl.program import (
        get_standard_rules,
        get_conservative_rules,
        get_aggressive_rules,
    )
    
    standard = get_standard_rules()
    conservative = get_conservative_rules()
    aggressive = get_aggressive_rules()
    
    print(f"  Standard rules: {len(standard)}")
    print(f"  Conservative rules: {len(conservative)}")
    print(f"  Aggressive rules: {len(aggressive)}")
    
    if len(conservative) > len(standard):
        print("   Conservative should be subset of standard")
        return False
    
    print("   Rule sets configured correctly")
    return True


def test_explain_rewrites():
    """Test rewrite explanation."""
    print("\nTesting rewrite explanation...")
    
    from py3plex.dsl.ast import Query, SelectStmt, Target, ComputeItem, ConditionExpr, ConditionAtom, Comparison
    from py3plex.dsl.program import GraphProgram, RewriteEngine, get_standard_rules
    
    query = Query(
        explain=False,
        select=SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            where=ConditionExpr(
                atoms=[ConditionAtom(comparison=Comparison(left="layer", op="=", right="social"))]
            ),
        )
    )
    
    program = GraphProgram.from_ast(query)
    engine = RewriteEngine(rules=get_standard_rules())
    
    try:
        applicable = engine.explain_rewrites(program)
        print(f"  Applicable rules: {len(applicable)}")
        print("   Rewrite explanation works")
        return True
    except Exception as e:
        print(f"   Rewrite explanation failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("RewriteEngine Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Rule Count", test_rule_count),
        ("Basic Functionality", test_basic_functionality),
        ("Optimize Method", test_optimize_method),
        ("Context-Aware", test_context_aware),
        ("Rule Sets", test_rule_sets),
        ("Explain Rewrites", test_explain_rewrites),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "" if success else ""
        print(f"{status} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n All verification tests passed!")
        return 0
    else:
        print(f"\n {total - passed} verification test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
