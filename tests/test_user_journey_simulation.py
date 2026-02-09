"""
Test the user journey simulation for ergonomics validation.

This ensures the simulation runs without errors and demonstrates
that users can successfully complete common tasks.
"""

import pytest
import sys
from pathlib import Path

# Import the simulation module
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))


def test_user_journey_simulation_runs():
    """Test that the user journey simulation runs without errors."""
    from examples.getting_started import user_journey_simulation
    
    # The simulation should return 0 on success
    result = user_journey_simulation.main()
    assert result == 0, "User journey simulation failed"


def test_first_time_user_journey():
    """Test the first-time user journey completes successfully."""
    from examples.getting_started import user_journey_simulation
    
    net = user_journey_simulation.simulate_first_time_user()
    assert net is not None
    layers = net.get_layers()[0]  # get_layers returns (layer_list, graphs, dict)
    nodes = list(net.get_nodes())
    assert len(layers) == 2
    assert len(nodes) == 8  # 4 people × 2 layers


def test_intermediate_user_journey():
    """Test the intermediate user journey completes successfully."""
    from examples.getting_started import user_journey_simulation
    
    net = user_journey_simulation.simulate_intermediate_user()
    assert net is not None
    layers = net.get_layers()[0]  # get_layers returns (layer_list, graphs, dict)
    nodes = list(net.get_nodes())
    assert len(layers) == 3
    assert len(nodes) > 0


def test_advanced_user_journey():
    """Test the advanced user journey completes successfully."""
    from examples.getting_started import user_journey_simulation
    
    net = user_journey_simulation.simulate_advanced_user()
    assert net is not None
    nodes = list(net.get_nodes())
    assert len(nodes) > 0


def test_ergonomic_improvements_documented():
    """Test that ergonomic improvements are documented."""
    from examples.getting_started import user_journey_simulation
    
    # Should not raise any errors
    user_journey_simulation.demonstrate_ergonomic_improvements()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
