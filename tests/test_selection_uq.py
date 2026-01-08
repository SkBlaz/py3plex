"""Unit tests for SelectionUQ core types and reducers.

This module tests the SelectionOutput, SelectionUQ, and reducer classes
to ensure they correctly compute uncertainty statistics.
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st

from py3plex.uncertainty.selection_types import SelectionOutput
from py3plex.uncertainty.selection_reducers import (
    InclusionReducer,
    SizeReducer,
    StabilityReducer,
    RankReducer,
    TopKOverlapReducer,
    GroupedReducer,
)
from py3plex.uncertainty.selection_uq import SelectionUQ
from py3plex.uncertainty.ci_utils import (
    wilson_score_interval,
    clopper_pearson_interval,
    binomial_proportion_ci,
)


class TestSelectionOutput:
    """Tests for SelectionOutput validation."""
    
    def test_basic_creation(self):
        """Test basic SelectionOutput creation."""
        sel = SelectionOutput(
            items=['a', 'b', 'c'],
            target='nodes'
        )
        assert len(sel.items) == 3
        assert sel.target == 'nodes'
        assert sel.scores is None
        assert sel.ranks is None
    
    def test_with_ranks(self):
        """Test SelectionOutput with ranks."""
        sel = SelectionOutput(
            items=['a', 'b', 'c'],
            ranks={'a': 1, 'b': 2, 'c': 3},
            k=3,
            target='nodes'
        )
        assert sel.ranks == {'a': 1, 'b': 2, 'c': 3}
        assert sel.k == 3
    
    def test_validation_k_without_ranks(self):
        """Test that k requires ranks."""
        with pytest.raises(ValueError, match="If k is specified"):
            SelectionOutput(
                items=['a', 'b', 'c'],
                k=3,
                target='nodes'
            )
    
    def test_validation_missing_ranks(self):
        """Test that all items must have ranks if ranks provided."""
        with pytest.raises(ValueError, match="Items missing ranks"):
            SelectionOutput(
                items=['a', 'b', 'c'],
                ranks={'a': 1, 'b': 2},  # Missing 'c'
                target='nodes'
            )


class TestInclusionReducer:
    """Tests for InclusionReducer."""
    
    def test_deterministic_selection(self):
        """Test that identical selections give present_prob=1."""
        reducer = InclusionReducer()
        
        # Add same selection 10 times
        for _ in range(10):
            sel = SelectionOutput(items=['a', 'b', 'c'], target='nodes')
            reducer.update(sel)
        
        result = reducer.finalize()
        
        assert result['n_samples'] == 10
        assert result['present_prob']['a'] == 1.0
        assert result['present_prob']['b'] == 1.0
        assert result['present_prob']['c'] == 1.0
    
    def test_varying_selection(self):
        """Test varying selections."""
        reducer = InclusionReducer()
        
        # 'a' appears 3 times, 'b' 2 times, 'c' 1 time
        selections = [
            ['a', 'b'],
            ['a', 'c'],
            ['a', 'b'],
        ]
        
        for items in selections:
            reducer.update(SelectionOutput(items=items, target='nodes'))
        
        result = reducer.finalize()
        
        assert result['n_samples'] == 3
        assert result['present_prob']['a'] == 1.0
        assert result['present_prob']['b'] == pytest.approx(2/3)
        assert result['present_prob']['c'] == pytest.approx(1/3)
    
    def test_empty_reducer(self):
        """Test empty reducer."""
        reducer = InclusionReducer()
        result = reducer.finalize()
        
        assert result['n_samples'] == 0
        assert result['present_prob'] == {}
        assert result['items_universe'] == []


class TestSizeReducer:
    """Tests for SizeReducer."""
    
    def test_constant_size(self):
        """Test selections with constant size."""
        reducer = SizeReducer()
        
        for _ in range(5):
            reducer.update(SelectionOutput(items=['a', 'b', 'c'], target='nodes'))
        
        result = reducer.finalize()
        
        assert result['mean'] == 3.0
        assert result['std'] == 0.0
    
    def test_varying_size(self):
        """Test selections with varying sizes."""
        reducer = SizeReducer(store_samples=True)
        
        sizes = [1, 2, 3, 4, 5]
        for size in sizes:
            items = list(range(size))
            reducer.update(SelectionOutput(items=items, target='nodes'))
        
        result = reducer.finalize()
        
        assert result['mean'] == 3.0
        assert result['std'] == pytest.approx(np.std([1, 2, 3, 4, 5], ddof=0))
        assert result['min'] == 1
        assert result['max'] == 5


class TestStabilityReducer:
    """Tests for StabilityReducer."""
    
    def test_identical_selections(self):
        """Test that identical selections give Jaccard=1."""
        reducer = StabilityReducer()
        
        for _ in range(5):
            reducer.update(SelectionOutput(items=['a', 'b', 'c'], target='nodes'))
        
        result = reducer.finalize()
        
        assert result['jaccard_mean'] == 1.0
        assert result['jaccard_std'] == 0.0
        assert result['consensus_size'] == 3
    
    def test_varying_selections(self):
        """Test varying selections."""
        reducer = StabilityReducer(consensus_threshold=0.5)
        
        selections = [
            ['a', 'b'],
            ['a', 'c'],
            ['a', 'b'],
            ['a', 'd'],
        ]
        
        for items in selections:
            reducer.update(SelectionOutput(items=items, target='nodes'))
        
        result = reducer.finalize()
        
        # 'a' appears 4 times (100%), so it's in consensus
        # 'b' appears 2 times (50%), so it's at the threshold (included)
        # Others appear 1 time (<50%), so not in consensus
        assert result['consensus_size'] >= 1  # At least 'a', possibly 'b' at boundary
        assert 0.0 < result['jaccard_mean'] < 1.0
        assert result['jaccard_std'] >= 0.0


class TestRankReducer:
    """Tests for RankReducer."""
    
    def test_constant_ranks(self):
        """Test constant ranks across samples."""
        reducer = RankReducer(k=3)
        
        for _ in range(5):
            sel = SelectionOutput(
                items=['a', 'b', 'c'],
                ranks={'a': 1, 'b': 2, 'c': 3},
                k=3,
                target='nodes'
            )
            reducer.update(sel)
        
        result = reducer.finalize()
        
        assert result['rank_mean']['a'] == 1.0
        assert result['rank_mean']['b'] == 2.0
        assert result['rank_mean']['c'] == 3.0
        assert result['rank_std']['a'] == 0.0
        assert result['p_in_topk']['a'] == 1.0
        assert result['p_in_topk']['b'] == 1.0
        assert result['p_in_topk']['c'] == 1.0
    
    def test_varying_ranks(self):
        """Test varying ranks."""
        reducer = RankReducer(k=2, store_samples=True)
        
        samples = [
            {'a': 1, 'b': 2, 'c': 3},
            {'a': 1, 'b': 3, 'c': 2},
            {'a': 2, 'b': 1, 'c': 3},
        ]
        
        for ranks in samples:
            sel = SelectionOutput(
                items=list(ranks.keys()),
                ranks=ranks,
                k=2,
                target='nodes'
            )
            reducer.update(sel)
        
        result = reducer.finalize()
        
        # Check means
        assert result['rank_mean']['a'] == pytest.approx((1 + 1 + 2) / 3)
        assert result['rank_mean']['b'] == pytest.approx((2 + 3 + 1) / 3)
        assert result['rank_mean']['c'] == pytest.approx((3 + 2 + 3) / 3)
        
        # Check p_in_topk (rank <= 2)
        assert result['p_in_topk']['a'] == 1.0  # Always in top-2
        assert result['p_in_topk']['b'] == pytest.approx(2/3)  # 2 out of 3 times
        assert result['p_in_topk']['c'] == pytest.approx(1/3)  # 1 out of 3 times


class TestTopKOverlapReducer:
    """Tests for TopKOverlapReducer."""
    
    def test_identical_topk(self):
        """Test identical top-k sets."""
        reducer = TopKOverlapReducer()
        
        for _ in range(3):
            sel = SelectionOutput(
                items=['a', 'b', 'c'],
                ranks={'a': 1, 'b': 2, 'c': 3},
                k=2,
                target='nodes'
            )
            reducer.update(sel)
        
        result = reducer.finalize()
        
        # All pairs have overlap = 2 (top-2 items are identical)
        assert result['overlap_mean'] == 2.0
        assert result['overlap_std'] == 0.0
    
    def test_varying_topk(self):
        """Test varying top-k sets."""
        reducer = TopKOverlapReducer(store_samples=True)
        
        samples = [
            {'a': 1, 'b': 2, 'c': 3},  # top-2: {a, b}
            {'b': 1, 'c': 2, 'a': 3},  # top-2: {b, c}
            {'a': 1, 'c': 2, 'b': 3},  # top-2: {a, c}
        ]
        
        for ranks in samples:
            sel = SelectionOutput(
                items=list(ranks.keys()),
                ranks=ranks,
                k=2,
                target='nodes'
            )
            reducer.update(sel)
        
        result = reducer.finalize()
        
        # Overlaps: {a,b}∩{b,c}=1, {a,b}∩{a,c}=1, {b,c}∩{a,c}=1
        assert result['overlap_mean'] == 1.0
        assert result['overlap_std'] == 0.0


class TestGroupedReducer:
    """Tests for GroupedReducer."""
    
    def test_grouped_inclusion(self):
        """Test grouped inclusion reducer."""
        reducer = GroupedReducer(InclusionReducer)
        
        # Group A
        for _ in range(3):
            sel = SelectionOutput(
                items=['a', 'b'],
                target='nodes',
                group_key=('A',)
            )
            reducer.update(sel)
        
        # Group B
        for _ in range(2):
            sel = SelectionOutput(
                items=['c', 'd'],
                target='nodes',
                group_key=('B',)
            )
            reducer.update(sel)
        
        results = reducer.finalize()
        
        assert ('A',) in results
        assert ('B',) in results
        
        assert results[('A',)]['n_samples'] == 3
        assert results[('A',)]['present_prob']['a'] == 1.0
        
        assert results[('B',)]['n_samples'] == 2
        assert results[('B',)]['present_prob']['c'] == 1.0


class TestCIUtils:
    """Tests for confidence interval utilities."""
    
    def test_wilson_interval_basic(self):
        """Test Wilson interval basic cases."""
        # 50 successes out of 100
        lower, upper = wilson_score_interval(50, 100, alpha=0.05)
        assert 0.4 < lower < 0.5
        assert 0.5 < upper < 0.6
        
        # 0 successes
        lower, upper = wilson_score_interval(0, 100, alpha=0.05)
        assert lower < 1e-6  # Effectively 0
        assert 0.0 < upper < 0.05
        
        # 100 successes
        lower, upper = wilson_score_interval(100, 100, alpha=0.05)
        assert 0.95 < lower < 1.0
        assert upper == 1.0
    
    def test_wilson_bounds(self):
        """Test that Wilson interval bounds are in [0, 1]."""
        for successes in [0, 10, 50, 90, 100]:
            lower, upper = wilson_score_interval(successes, 100, alpha=0.05)
            assert 0.0 <= lower <= 1.0
            assert 0.0 <= upper <= 1.0
            assert lower <= upper
    
    def test_clopper_pearson(self):
        """Test Clopper-Pearson interval."""
        lower, upper = clopper_pearson_interval(50, 100, alpha=0.05)
        # Clopper-Pearson is conservative, so slightly wider interval
        assert 0.39 < lower < 0.5
        assert 0.5 < upper < 0.61
    
    def test_binomial_proportion_ci(self):
        """Test binomial_proportion_ci wrapper."""
        lower_w, upper_w = binomial_proportion_ci(50, 100, method="wilson")
        lower_cp, upper_cp = binomial_proportion_ci(50, 100, method="clopper-pearson")
        
        # Both should be valid
        assert 0.0 <= lower_w <= 1.0
        assert 0.0 <= upper_w <= 1.0
        assert 0.0 <= lower_cp <= 1.0
        assert 0.0 <= upper_cp <= 1.0


class TestSelectionUQ:
    """Tests for SelectionUQ class."""
    
    def test_basic_creation(self):
        """Test basic SelectionUQ creation."""
        uq = SelectionUQ(
            n_samples=10,
            items_universe=['a', 'b', 'c'],
            samples_seen=10,
            present_prob={'a': 1.0, 'b': 0.8, 'c': 0.5},
            size_stats={'mean': 2.5, 'std': 0.5},
            stability_stats={'jaccard_mean': 0.9, 'jaccard_std': 0.1},
        )
        
        assert uq.n_samples == 10
        assert len(uq.items_universe) == 3
        assert uq.present_prob['a'] == 1.0
    
    def test_from_reducers(self):
        """Test construction from reducers."""
        inclusion_result = {
            'n_samples': 5,
            'items_universe': ['a', 'b', 'c'],
            'present_prob': {'a': 1.0, 'b': 0.8, 'c': 0.4},
        }
        
        size_result = {'mean': 2.5, 'std': 0.5}
        
        stability_result = {
            'jaccard_mean': 0.9,
            'jaccard_std': 0.1,
            'consensus_size': 2,
        }
        
        uq = SelectionUQ.from_reducers(
            inclusion_result=inclusion_result,
            size_result=size_result,
            stability_result=stability_result,
            consensus_threshold=0.5,
            target='nodes',
        )
        
        assert uq.n_samples == 5
        assert len(uq.consensus_items) == 2  # a and b
        assert 'c' in uq.borderline_items  # 0.4 is near 0.5
    
    def test_summary(self):
        """Test summary method."""
        uq = SelectionUQ(
            n_samples=10,
            items_universe=['a', 'b', 'c'],
            samples_seen=10,
            present_prob={'a': 1.0, 'b': 0.8, 'c': 0.5},
            size_stats={'mean': 2.5, 'std': 0.5},
            stability_stats={'jaccard_mean': 0.9, 'jaccard_std': 0.1},
            consensus_items={'a', 'b'},
            borderline_items=['c'],
        )
        
        summary = uq.summary()
        
        assert summary['n_samples'] == 10
        assert summary['n_items_universe'] == 3
        assert summary['consensus']['size'] == 2
        assert summary['borderline']['count'] == 1
    
    def test_to_pandas(self):
        """Test to_pandas method."""
        uq = SelectionUQ(
            n_samples=10,
            items_universe=['a', 'b', 'c'],
            samples_seen=10,
            present_prob={'a': 1.0, 'b': 0.8, 'c': 0.5},
            present_ci_low={'a': 0.95, 'b': 0.6, 'c': 0.3},
            present_ci_high={'a': 1.0, 'b': 0.9, 'c': 0.7},
            size_stats={'mean': 2.5, 'std': 0.5},
            stability_stats={'jaccard_mean': 0.9, 'jaccard_std': 0.1},
        )
        
        df = uq.to_pandas(expand=True)
        
        assert len(df) == 3
        assert 'item' in df.columns
        assert 'present_prob' in df.columns
        assert 'present_ci_low' in df.columns
        assert 'present_ci_high' in df.columns
        
        assert df[df['item'] == 'a']['present_prob'].iloc[0] == 1.0


# Property-based tests
@pytest.mark.property
class TestSelectionUQProperties:
    """Property-based tests for SelectionUQ."""
    
    @given(
        n_samples=st.integers(min_value=1, max_value=100),
        n_items=st.integers(min_value=1, max_value=20),
    )
    def test_present_prob_bounds(self, n_samples, n_items):
        """Test that present_prob is always in [0, 1]."""
        reducer = InclusionReducer()
        
        items = [f"item_{i}" for i in range(n_items)]
        
        for _ in range(n_samples):
            # Randomly select subset
            import random
            selected = random.sample(items, k=random.randint(0, n_items))
            reducer.update(SelectionOutput(items=selected, target='nodes'))
        
        result = reducer.finalize()
        
        for item, prob in result['present_prob'].items():
            assert 0.0 <= prob <= 1.0
    
    @given(
        n_samples=st.integers(min_value=5, max_value=50),
        n_items=st.integers(min_value=2, max_value=10),
    )
    def test_wilson_ci_bounds(self, n_samples, n_items):
        """Test that Wilson CI bounds are valid."""
        reducer = InclusionReducer()
        
        items = [f"item_{i}" for i in range(n_items)]
        
        for _ in range(n_samples):
            import random
            selected = random.sample(items, k=random.randint(0, n_items))
            reducer.update(SelectionOutput(items=selected, target='nodes'))
        
        result = reducer.finalize()
        
        for item, prob in result['present_prob'].items():
            successes = int(round(prob * n_samples))
            lower, upper = wilson_score_interval(successes, n_samples)
            
            assert 0.0 <= lower <= 1.0
            assert 0.0 <= upper <= 1.0
            assert lower <= upper
            assert lower <= prob <= upper or abs(prob - lower) < 0.01  # Allow small tolerance
