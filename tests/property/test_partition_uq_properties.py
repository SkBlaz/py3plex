"""
Property-based tests for PartitionUQ.

Tests fundamental properties and invariants of partition uncertainty quantification
using Hypothesis for property-based testing.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

from py3plex.uncertainty import (
    PartitionUQ,
    partition_dict_to_array,
    partition_array_to_dict,
)
from py3plex.uncertainty.partition_metrics import (
    variation_of_information,
    normalized_mutual_information,
)
from py3plex.uncertainty.partition_reducers import (
    NodeEntropyReducer,
    CoAssignmentReducer,
    ConsensusReducer,
)
from py3plex.uncertainty.noise_models import (
    EdgeDrop,
    WeightNoise,
    LayerDrop,
)


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def partition_strategy(draw, min_nodes=3, max_nodes=20, min_communities=1, max_communities=5):
    """Generate valid partition arrays."""
    n_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    n_communities = draw(st.integers(min_value=min_communities, max_value=max_communities))
    
    # Ensure n_communities <= n_nodes
    n_communities = min(n_communities, n_nodes)
    
    # Generate partition with at least one node per community
    partition = []
    # First assign one node to each community
    for i in range(n_communities):
        partition.append(i)
    # Then randomly assign remaining nodes
    for i in range(n_communities, n_nodes):
        partition.append(draw(st.integers(min_value=0, max_value=n_communities - 1)))
    
    # Shuffle to avoid patterns
    draw(st.randoms()).shuffle(partition)
    
    return np.array(partition, dtype=np.int32)


@st.composite
def partition_list_strategy(draw, min_partitions=2, max_partitions=10, n_nodes=None):
    """Generate a list of partitions for the same nodes."""
    if n_nodes is None:
        n_nodes = draw(st.integers(min_value=3, max_value=15))
    
    n_partitions = draw(st.integers(min_value=min_partitions, max_value=max_partitions))
    
    partitions = []
    for _ in range(n_partitions):
        partition = draw(partition_strategy(min_nodes=n_nodes, max_nodes=n_nodes))
        partitions.append(partition)
    
    return partitions, n_nodes


@st.composite
def node_ids_strategy(draw, n_nodes):
    """Generate node IDs."""
    return [f"node_{i}" for i in range(n_nodes)]


# ============================================================================
# Partition Distance Metrics Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(partition=partition_strategy())
def test_vi_self_distance_zero(partition):
    """VI(P, P) = 0 for any partition P."""
    vi = variation_of_information(partition, partition)
    assert abs(vi) < 1e-10, f"VI self-distance should be zero, got {vi}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(n=st.integers(min_value=3, max_value=15), data=st.data())
def test_vi_symmetry(n, data):
    """VI(P1, P2) = VI(P2, P1)."""
    # Generate two partitions of the same size
    p1 = data.draw(partition_strategy(min_nodes=n, max_nodes=n))
    p2 = data.draw(partition_strategy(min_nodes=n, max_nodes=n))
    
    vi_12 = variation_of_information(p1, p2)
    vi_21 = variation_of_information(p2, p1)
    
    assert abs(vi_12 - vi_21) < 1e-10, \
        f"VI not symmetric: VI(P1,P2)={vi_12}, VI(P2,P1)={vi_21}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(partition=partition_strategy())
def test_vi_non_negative(partition):
    """VI(P1, P2) >= 0 for any partitions."""
    # Create a different partition
    p2 = partition.copy()
    if len(p2) > 1:
        p2[0] = (p2[0] + 1) % (partition.max() + 2)
    
    vi = variation_of_information(partition, p2)
    assert vi >= 0, f"VI should be non-negative, got {vi}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(partition=partition_strategy())
def test_nmi_self_similarity_one(partition):
    """NMI(P, P) = 1 for any partition P."""
    nmi = normalized_mutual_information(partition, partition)
    assert abs(nmi - 1.0) < 1e-10, f"NMI self-similarity should be 1, got {nmi}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(n=st.integers(min_value=3, max_value=15), data=st.data())
def test_nmi_bounds(n, data):
    """NMI(P1, P2) ∈ [0, 1]."""
    # Generate two partitions of the same size
    p1 = data.draw(partition_strategy(min_nodes=n, max_nodes=n))
    p2 = data.draw(partition_strategy(min_nodes=n, max_nodes=n))
    
    nmi = normalized_mutual_information(p1, p2)
    assert 0 <= nmi <= 1, f"NMI should be in [0, 1], got {nmi}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(n=st.integers(min_value=3, max_value=15), data=st.data())
def test_nmi_symmetry(n, data):
    """NMI(P1, P2) = NMI(P2, P1)."""
    # Generate two partitions of the same size
    p1 = data.draw(partition_strategy(min_nodes=n, max_nodes=n))
    p2 = data.draw(partition_strategy(min_nodes=n, max_nodes=n))
    
    nmi_12 = normalized_mutual_information(p1, p2)
    nmi_21 = normalized_mutual_information(p2, p1)
    
    assert abs(nmi_12 - nmi_21) < 1e-10, \
        f"NMI not symmetric: NMI(P1,P2)={nmi_12}, NMI(P2,P1)={nmi_21}"


# ============================================================================
# Partition Conversion Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(partition=partition_strategy())
def test_partition_conversion_roundtrip(partition):
    """Converting partition array -> dict -> array should be identity."""
    n_nodes = len(partition)
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    # Array -> Dict
    partition_dict = partition_array_to_dict(partition, node_ids)
    
    # Dict -> Array
    partition_back = partition_dict_to_array(partition_dict, node_ids)
    
    assert np.array_equal(partition, partition_back), \
        "Partition conversion roundtrip failed"


# ============================================================================
# PartitionReducer Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_node_entropy_reducer_deterministic(data):
    """Entropy should be zero when all samples are identical."""
    partitions, n_nodes = data
    
    # Make all partitions identical
    partitions = [partitions[0].copy() for _ in partitions]
    
    reducer = NodeEntropyReducer(n_nodes)
    for partition in partitions:
        reducer.update(partition)
    
    entropy = reducer.finalize()
    
    # All nodes should have zero entropy
    assert np.allclose(entropy, 0.0), \
        f"Entropy should be zero for deterministic samples, got {entropy}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_node_entropy_reducer_non_negative(data):
    """Entropy must be non-negative."""
    partitions, n_nodes = data
    
    reducer = NodeEntropyReducer(n_nodes)
    for partition in partitions:
        reducer.update(partition)
    
    entropy = reducer.finalize()
    
    assert np.all(entropy >= 0), f"Found negative entropy: {entropy[entropy < 0]}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_consensus_reducer_mode_property(data):
    """Consensus label should be the most frequent label for each node."""
    partitions, n_nodes = data
    
    reducer = ConsensusReducer(n_nodes)
    for partition in partitions:
        reducer.update(partition)
    
    consensus = reducer.finalize()
    
    # Verify consensus is the mode
    for i in range(n_nodes):
        labels = [p[i] for p in partitions]
        label_counts = {}
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        most_frequent = max(label_counts, key=label_counts.get)
        assert consensus[i] == most_frequent, \
            f"Node {i}: consensus={consensus[i]}, mode={most_frequent}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.too_slow])
@given(data=partition_list_strategy(max_partitions=5))
def test_coassignment_reducer_diagonal_one(data):
    """Co-assignment diagonal should always be 1 (P(i,i) = 1)."""
    partitions, n_nodes = data
    
    reducer = CoAssignmentReducer(n_nodes, sparse=False)
    for partition in partitions:
        reducer.update(partition)
    
    coassoc = reducer.finalize()
    
    diagonal = np.diag(coassoc)
    assert np.allclose(diagonal, 1.0), \
        f"Co-assignment diagonal should be all 1s, got {diagonal}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.too_slow])
@given(data=partition_list_strategy(max_partitions=5))
def test_coassignment_reducer_symmetric(data):
    """Co-assignment matrix should be symmetric: P(i,j) = P(j,i)."""
    partitions, n_nodes = data
    
    reducer = CoAssignmentReducer(n_nodes, sparse=False)
    for partition in partitions:
        reducer.update(partition)
    
    coassoc = reducer.finalize()
    
    assert np.allclose(coassoc, coassoc.T), \
        "Co-assignment matrix not symmetric"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.too_slow])
@given(data=partition_list_strategy(max_partitions=5))
def test_coassignment_reducer_bounds(data):
    """Co-assignment probabilities should be in [0, 1]."""
    partitions, n_nodes = data
    
    reducer = CoAssignmentReducer(n_nodes, sparse=False)
    for partition in partitions:
        reducer.update(partition)
    
    coassoc = reducer.finalize()
    
    assert np.all(coassoc >= 0) and np.all(coassoc <= 1), \
        "Co-assignment probabilities outside [0, 1]"


# ============================================================================
# PartitionUQ Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_entropy_bounds(data):
    """PartitionUQ entropy should be non-negative."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    assert np.all(uq.membership_entropy >= 0), \
        f"Found negative entropy: {uq.membership_entropy[uq.membership_entropy < 0]}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_confidence_bounds(data):
    """PartitionUQ confidence should be in [0, 1]."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    assert np.all(uq.p_max_membership >= 0) and np.all(uq.p_max_membership <= 1), \
        f"Confidence outside [0, 1]: min={uq.p_max_membership.min()}, max={uq.p_max_membership.max()}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_deterministic_confidence_one(data):
    """When all samples identical, all nodes should have confidence=1."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    # Make all partitions identical
    partitions = [partitions[0].copy() for _ in partitions]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    assert np.allclose(uq.p_max_membership, 1.0), \
        f"Deterministic samples should have confidence=1, got {uq.p_max_membership}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_deterministic_entropy_zero(data):
    """When all samples identical, all nodes should have entropy=0."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    # Make all partitions identical
    partitions = [partitions[0].copy() for _ in partitions]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    assert np.allclose(uq.membership_entropy, 0.0), \
        f"Deterministic samples should have entropy=0, got {uq.membership_entropy}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_consensus_is_mode(data):
    """Consensus partition should assign each node to its most frequent community."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="samples"
    )
    
    # Verify consensus matches mode
    for i in range(n_nodes):
        labels = [p[i] for p in uq.samples]
        label_counts = {}
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        most_frequent = max(label_counts, key=label_counts.get)
        assert uq.consensus_partition[i] == most_frequent, \
            f"Node {i}: consensus={uq.consensus_partition[i]}, mode={most_frequent}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_vi_nmi_consistency(data):
    """When VI is low, NMI should be high (inverse relationship)."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    # Need at least 2 distinct partitions for this test
    assume(not all(np.array_equal(partitions[0], p) for p in partitions))
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    # When all samples are very similar (VI ≈ 0), NMI should be high (≈ 1)
    # When samples are very different (VI high), NMI should be lower
    # They should be inversely correlated
    if uq.vi_mean < 0.1:
        assert uq.nmi_mean > 0.7, \
            f"Low VI ({uq.vi_mean}) should imply high NMI, got {uq.nmi_mean}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy())
def test_partition_uq_stability_non_negative(data):
    """Stability metrics should be non-negative."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    assert uq.vi_mean >= 0, f"VI mean should be non-negative, got {uq.vi_mean}"
    assert uq.vi_std >= 0, f"VI std should be non-negative, got {uq.vi_std}"
    assert 0 <= uq.nmi_mean <= 1, f"NMI mean should be in [0,1], got {uq.nmi_mean}"
    assert uq.nmi_std >= 0, f"NMI std should be non-negative, got {uq.nmi_std}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(data=partition_list_strategy(min_partitions=3, max_partitions=6))
def test_partition_uq_n_communities_reasonable(data):
    """Consensus should have reasonable number of communities."""
    partitions, n_nodes = data
    node_ids = [f"node_{i}" for i in range(n_nodes)]
    
    uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store="none"
    )
    
    # Should have at least 1 community
    assert uq.n_communities >= 1, \
        f"Should have at least 1 community, got {uq.n_communities}"
    
    # Should not have more communities than nodes
    assert uq.n_communities <= n_nodes, \
        f"Cannot have more communities ({uq.n_communities}) than nodes ({n_nodes})"


# ============================================================================
# NoiseModel Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(p=st.floats(min_value=0.01, max_value=0.99))
def test_edge_drop_serialization_roundtrip(p):
    """EdgeDrop serialization should be reversible."""
    from py3plex.uncertainty.noise_models import noise_model_from_dict
    
    noise = EdgeDrop(p=p)
    data = noise.to_dict()
    
    noise2 = noise_model_from_dict(data)
    
    assert isinstance(noise2, EdgeDrop)
    assert noise2.p == p


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    sigma=st.floats(min_value=0.01, max_value=2.0),
    dist=st.sampled_from(["lognormal", "uniform", "normal"])
)
def test_weight_noise_serialization_roundtrip(sigma, dist):
    """WeightNoise serialization should be reversible."""
    from py3plex.uncertainty.noise_models import noise_model_from_dict
    
    noise = WeightNoise(dist=dist, sigma=sigma)
    data = noise.to_dict()
    
    noise2 = noise_model_from_dict(data)
    
    assert isinstance(noise2, WeightNoise)
    assert noise2.sigma == sigma
    assert noise2.dist == dist


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(p=st.floats(min_value=0.01, max_value=0.99))
def test_layer_drop_serialization_roundtrip(p):
    """LayerDrop serialization should be reversible."""
    from py3plex.uncertainty.noise_models import noise_model_from_dict
    
    noise = LayerDrop(p=p)
    data = noise.to_dict()
    
    noise2 = noise_model_from_dict(data)
    
    assert isinstance(noise2, LayerDrop)
    assert noise2.p == p
