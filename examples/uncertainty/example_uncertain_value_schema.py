"""
Example: UncertainValue and Schema Constants

This example demonstrates the new low-level uncertainty primitives:
1. UncertainValue - representing individual values with uncertainty
2. Schema constants - canonical attribute names for uncertain networks

These are building blocks for uncertainty-native computation in py3plex.
"""

import numpy as np
from py3plex.core import multinet
from py3plex.uncertainty import UncertainValue, schema


def example_1_deterministic_value():
    """Example 1: Deterministic UncertainValue (no uncertainty)."""
    print("\n" + "="*70)
    print("Example 1: Deterministic Value")
    print("="*70)
    
    # Create a deterministic value
    v = UncertainValue(kind="deterministic", params={"value": 5.0})
    
    print(f"\nValue: {v}")
    print(f"Mean: {v.mean()}")
    print(f"Variance: {v.var()}")
    print(f"Std: {v.std()}")
    print(f"Is deterministic? {v.is_deterministic()}")
    
    # Sampling always returns the same value
    rng = np.random.default_rng(42)
    samples = v.sample(rng, n=5)
    print(f"\n5 samples: {samples}")
    print("(All samples are identical for deterministic values)")


def example_2_bernoulli_distribution():
    """Example 2: Bernoulli distribution for edge existence probability."""
    print("\n" + "="*70)
    print("Example 2: Bernoulli Distribution (Edge Existence)")
    print("="*70)
    
    # Create a Bernoulli distribution (probability of edge existing)
    p_exist = 0.75
    v = UncertainValue(kind="bernoulli", params={"p": p_exist})
    
    print(f"\nEdge existence probability: {p_exist}")
    print(f"Mean (expected value): {v.mean()}")
    print(f"Variance: {v.var():.4f}")
    print(f"Std: {v.std():.4f}")
    
    # Sample to simulate edge existence
    rng = np.random.default_rng(42)
    samples = v.sample(rng, n=20)
    print(f"\n20 samples (1=exists, 0=absent): {samples}")
    print(f"Fraction existing: {np.mean(samples):.2f} (should be ~{p_exist})")


def example_3_normal_distribution():
    """Example 3: Normal distribution for uncertain edge weights."""
    print("\n" + "="*70)
    print("Example 3: Normal Distribution (Uncertain Weight)")
    print("="*70)
    
    # Create a normal distribution for an uncertain edge weight
    mu, sigma = 2.5, 0.5
    v = UncertainValue(kind="normal", params={"mu": mu, "sigma": sigma})
    
    print(f"\nWeight: N(μ={mu}, σ={sigma})")
    print(f"Mean: {v.mean()}")
    print(f"Std: {v.std()}")
    
    # Sample possible weight values
    rng = np.random.default_rng(42)
    samples = v.sample(rng, n=10)
    print(f"\n10 sampled weights:")
    for i, s in enumerate(samples, 1):
        print(f"  Sample {i}: {s:.3f}")
    
    print(f"\nSample mean: {np.mean(samples):.3f} (should be ~{mu})")
    print(f"Sample std: {np.std(samples):.3f} (should be ~{sigma})")


def example_4_empirical_distribution():
    """Example 4: Empirical distribution from observed data."""
    print("\n" + "="*70)
    print("Example 4: Empirical Distribution (From Data)")
    print("="*70)
    
    # Create an empirical distribution from observed measurements
    observed_data = np.array([1.2, 2.3, 2.5, 2.8, 3.1, 3.4, 2.9, 2.1])
    v = UncertainValue(kind="empirical", params={"samples": observed_data})
    
    print(f"\nObserved data: {observed_data}")
    print(f"Mean: {v.mean():.3f}")
    print(f"Std: {v.std():.3f}")
    
    # Resample from the empirical distribution (bootstrap)
    rng = np.random.default_rng(42)
    resamples = v.sample(rng, n=10)
    print(f"\n10 bootstrap resamples:")
    for i, s in enumerate(resamples, 1):
        print(f"  Resample {i}: {s:.3f}")


def example_5_serialization():
    """Example 5: Serializing and deserializing UncertainValue."""
    print("\n" + "="*70)
    print("Example 5: Serialization")
    print("="*70)
    
    # Create an uncertain value
    v1 = UncertainValue(kind="normal", params={"mu": 10.0, "sigma": 2.0})
    
    # Convert to dictionary (JSON-serializable)
    d = v1.to_dict()
    print(f"\nOriginal: {v1}")
    print(f"As dict: {d}")
    
    # Reconstruct from dictionary
    v2 = UncertainValue.from_dict(d)
    print(f"Reconstructed: {v2}")
    print(f"Mean preserved: {v2.mean()} == {v1.mean()}")


def example_6_schema_constants():
    """Example 6: Using schema constants for edge attributes."""
    print("\n" + "="*70)
    print("Example 6: Schema Constants for Edges")
    print("="*70)
    
    # Create edge data with uncertainty using schema constants
    edge_data = {
        schema.WEIGHT_MEAN: 2.5,
        schema.WEIGHT_VAR: 0.1,
        schema.P_EXIST: 0.85,
        schema.UNCERTAINTY_SOURCE: "bootstrap",
        schema.N_SAMPLES: 100,
    }
    
    print("\nEdge with uncertainty:")
    for key, value in edge_data.items():
        print(f"  {key}: {value}")
    
    # Use schema helper functions
    weight = schema.get_edge_weight(edge_data)
    prob = schema.get_edge_existence_prob(edge_data)
    is_det = schema.is_deterministic_edge(edge_data)
    
    print(f"\nExtracted values:")
    print(f"  Weight: {weight}")
    print(f"  Existence probability: {prob}")
    print(f"  Is deterministic? {is_det}")


def example_7_backward_compatibility():
    """Example 7: Backward compatibility with legacy 'certainty' attribute."""
    print("\n" + "="*70)
    print("Example 7: Backward Compatibility")
    print("="*70)
    
    # Old code might use 'certainty' instead of 'p_exist'
    legacy_edge = {
        "weight": 1.5,
        "certainty": 0.7,  # legacy attribute
    }
    
    print("\nLegacy edge data:")
    for key, value in legacy_edge.items():
        print(f"  {key}: {value}")
    
    # Schema helpers handle legacy attributes
    weight = schema.get_edge_weight(legacy_edge)
    prob = schema.get_edge_existence_prob(legacy_edge)
    
    print(f"\nExtracted values (with legacy support):")
    print(f"  Weight: {weight}")
    print(f"  Existence probability (from 'certainty'): {prob}")
    
    # Modern code should use schema.P_EXIST
    modern_edge = {
        schema.WEIGHT_MEAN: 1.5,
        schema.P_EXIST: 0.7,
    }
    
    print("\nModern edge data (recommended):")
    for key, value in modern_edge.items():
        print(f"  {key}: {value}")


def example_8_network_with_uncertainty():
    """Example 8: Creating a network with uncertain edges."""
    print("\n" + "="*70)
    print("Example 8: Network with Uncertain Edges")
    print("="*70)
    
    # Create network
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "A", "type": "L1"},
        {"source": "B", "type": "L1"},
        {"source": "C", "type": "L1"},
    ])
    
    # Add edges with uncertainty attributes
    net.core_network.add_edge(
        ("A", "L1"), ("B", "L1"),
        **{
            schema.WEIGHT_MEAN: 2.0,
            schema.WEIGHT_VAR: 0.2,
            schema.P_EXIST: 0.90,
        }
    )
    
    net.core_network.add_edge(
        ("B", "L1"), ("C", "L1"),
        **{
            schema.WEIGHT_MEAN: 1.5,
            schema.WEIGHT_VAR: 0.1,
            schema.P_EXIST: 0.75,
        }
    )
    
    print("\nNetwork with uncertain edges created.")
    print(f"Nodes: {list(net.get_nodes())}")
    
    # Retrieve and display edge attributes
    print("\nEdge attributes:")
    for u, v, key, data in net.core_network.edges(keys=True, data=True):
        print(f"\n  Edge {u} -> {v}:")
        weight = schema.get_edge_weight(data)
        prob = schema.get_edge_existence_prob(data)
        print(f"    Weight: {weight}")
        print(f"    Existence prob: {prob}")
        
        if schema.WEIGHT_VAR in data:
            print(f"    Weight variance: {data[schema.WEIGHT_VAR]}")


def example_9_combining_uncertain_values():
    """Example 9: Combining UncertainValue with schema in a network."""
    print("\n" + "="*70)
    print("Example 9: UncertainValue + Schema Integration")
    print("="*70)
    
    # Create UncertainValue objects
    weight_dist = UncertainValue(
        kind="normal",
        params={"mu": 2.5, "sigma": 0.3}
    )
    
    exist_dist = UncertainValue(
        kind="bernoulli",
        params={"p": 0.8}
    )
    
    # Store in edge data using schema constants
    edge_data = {
        schema.WEIGHT_DIST: weight_dist,  # Full distribution
        schema.P_EXIST: exist_dist.mean(),  # Expected existence
    }
    
    print("\nEdge with full weight distribution:")
    print(f"  Weight distribution: {weight_dist}")
    print(f"  Weight mean: {weight_dist.mean()}")
    print(f"  Weight std: {weight_dist.std():.3f}")
    print(f"  Existence probability: {exist_dist.mean()}")
    
    # Sample from the distributions
    rng = np.random.default_rng(42)
    print("\nSampling from distributions:")
    for i in range(3):
        w = weight_dist.sample(rng, n=1)[0]
        exists = exist_dist.sample(rng, n=1)[0]
        print(f"  Sample {i+1}: weight={w:.3f}, exists={bool(exists)}")


def example_10_attribute_groups():
    """Example 10: Using attribute group constants."""
    print("\n" + "="*70)
    print("Example 10: Attribute Groups (Immutable Sets)")
    print("="*70)
    
    # Schema provides immutable attribute groups
    print("\nEdge uncertainty attributes:")
    for attr in sorted(schema.EDGE_UNCERTAINTY_ATTRS):
        print(f"  - {attr}")
    
    print("\nNode uncertainty attributes:")
    for attr in sorted(schema.NODE_UNCERTAINTY_ATTRS):
        print(f"  - {attr}")
    
    print("\nStat uncertainty attributes:")
    for attr in sorted(schema.STAT_UNCERTAINTY_ATTRS):
        print(f"  - {attr}")
    
    # Check if an attribute is uncertainty-related
    print("\nChecking attribute types:")
    attrs_to_check = ["weight", "weight_mean", "p_exist", "label", "color"]
    for attr in attrs_to_check:
        is_unc = schema.is_uncertainty_attr(attr)
        print(f"  '{attr}': {'uncertainty' if is_unc else 'regular'}")
    
    # Note: attribute groups are frozensets (immutable)
    print(f"\nAttribute groups are immutable (frozenset):")
    print(f"  Type: {type(schema.EDGE_UNCERTAINTY_ATTRS).__name__}")


def main():
    """Run all examples."""
    print("\n" + "#"*70)
    print("# UncertainValue and Schema Examples")
    print("#"*70)
    
    example_1_deterministic_value()
    example_2_bernoulli_distribution()
    example_3_normal_distribution()
    example_4_empirical_distribution()
    example_5_serialization()
    example_6_schema_constants()
    example_7_backward_compatibility()
    example_8_network_with_uncertainty()
    example_9_combining_uncertain_values()
    example_10_attribute_groups()
    
    print("\n" + "#"*70)
    print("# All examples completed successfully!")
    print("#"*70 + "\n")


if __name__ == "__main__":
    main()
