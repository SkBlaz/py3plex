"""Dataset utilities for the DSL Query Zoo.

This module provides functions to create small, reproducible multilayer networks
for testing and demonstrating DSL queries. All networks use fixed random seeds
for reproducibility.
"""

import numpy as np
import networkx as nx
from py3plex.core import multinet


def create_social_work_network(seed=42):
    """Create a small social-work multilayer network.
    
    This network represents people connected through:
    - Social relationships (friendships)
    - Work relationships (colleagues)
    - Family relationships
    
    Network properties:
    - 12 nodes across 3 layers
    - Some nodes appear in multiple layers (cross-layer presence)
    - Different connectivity patterns in each layer
    
    Args:
        seed: Random seed for reproducibility
        
    Returns:
        multi_layer_network: The constructed network
    """
    np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Define nodes for each layer
    people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 
              'Grace', 'Henry', 'Iris', 'Jack', 'Kate', 'Leo']
    
    # Social layer - dense connections among friends
    social_edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Frank', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Grace', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Henry', 'target': 'Iris', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Jack', 'target': 'Kate', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Kate', 'target': 'Leo', 'source_type': 'social', 'target_type': 'social'},
    ]
    
    # Work layer - different connectivity pattern
    work_edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Alice', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Alice', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Charlie', 'target': 'Grace', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Eve', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Grace', 'target': 'Henry', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Iris', 'target': 'Jack', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Jack', 'target': 'Kate', 'source_type': 'work', 'target_type': 'work'},
    ]
    
    # Family layer - sparse, small groups
    family_edges = [
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Bob', 'target': 'Eve', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'David', 'target': 'Frank', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Grace', 'target': 'Iris', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Henry', 'target': 'Iris', 'source_type': 'family', 'target_type': 'family'},
        {'source': 'Kate', 'target': 'Leo', 'source_type': 'family', 'target_type': 'family'},
    ]
    
    # Add all edges to the network
    network.add_edges(social_edges + work_edges + family_edges)
    
    return network


def create_communication_network(seed=42):
    """Create a communication multilayer network.
    
    This network represents communication through different channels:
    - Email (formal communication)
    - Chat (informal communication)
    - Phone (direct communication)
    
    Network properties:
    - 10 nodes across 3 layers
    - Star-like structure in email (centralized)
    - More distributed in chat and phone
    - Demonstrates different centrality patterns per layer
    
    Args:
        seed: Random seed for reproducibility
        
    Returns:
        multi_layer_network: The constructed network
    """
    np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    people = ['Manager', 'Dev1', 'Dev2', 'Dev3', 'Designer', 
              'Marketing1', 'Marketing2', 'Support1', 'Support2', 'HR']
    
    # Email - star topology with Manager at center
    email_edges = [
        {'source': 'Manager', 'target': person, 'source_type': 'email', 'target_type': 'email'}
        for person in people if person != 'Manager'
    ]
    
    # Chat - more distributed, team-based
    chat_edges = [
        {'source': 'Dev1', 'target': 'Dev2', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Dev2', 'target': 'Dev3', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Dev1', 'target': 'Dev3', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Designer', 'target': 'Dev1', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Marketing1', 'target': 'Marketing2', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Marketing1', 'target': 'Designer', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Support1', 'target': 'Support2', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Support1', 'target': 'Dev1', 'source_type': 'chat', 'target_type': 'chat'},
        {'source': 'Manager', 'target': 'Dev1', 'source_type': 'chat', 'target_type': 'chat'},
    ]
    
    # Phone - selective, important connections
    phone_edges = [
        {'source': 'Manager', 'target': 'Dev1', 'source_type': 'phone', 'target_type': 'phone'},
        {'source': 'Manager', 'target': 'Marketing1', 'source_type': 'phone', 'target_type': 'phone'},
        {'source': 'Manager', 'target': 'HR', 'source_type': 'phone', 'target_type': 'phone'},
        {'source': 'Dev1', 'target': 'Dev2', 'source_type': 'phone', 'target_type': 'phone'},
        {'source': 'Marketing1', 'target': 'Designer', 'source_type': 'phone', 'target_type': 'phone'},
        {'source': 'Support1', 'target': 'Manager', 'source_type': 'phone', 'target_type': 'phone'},
    ]
    
    network.add_edges(email_edges + chat_edges + phone_edges)
    
    return network


def create_transport_network(seed=42):
    """Create a transport multilayer network.
    
    This network represents a city's transport system with:
    - Bus routes
    - Metro lines
    - Walking paths
    
    Network properties:
    - 8 locations across 3 layers
    - Some locations accessible by multiple transport modes
    - Different efficiency/connectivity per layer
    
    Args:
        seed: Random seed for reproducibility
        
    Returns:
        multi_layer_network: The constructed network
    """
    np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    locations = ['CentralStation', 'ShoppingMall', 'Park', 'University',
                 'Hospital', 'Airport', 'BusinessDistrict', 'ResidentialArea']
    
    # Bus - covers most locations but slower
    bus_edges = [
        {'source': 'CentralStation', 'target': 'ShoppingMall', 'source_type': 'bus', 'target_type': 'bus'},
        {'source': 'ShoppingMall', 'target': 'Park', 'source_type': 'bus', 'target_type': 'bus'},
        {'source': 'Park', 'target': 'University', 'source_type': 'bus', 'target_type': 'bus'},
        {'source': 'CentralStation', 'target': 'Hospital', 'source_type': 'bus', 'target_type': 'bus'},
        {'source': 'Hospital', 'target': 'Airport', 'source_type': 'bus', 'target_type': 'bus'},
        {'source': 'CentralStation', 'target': 'ResidentialArea', 'source_type': 'bus', 'target_type': 'bus'},
        {'source': 'ResidentialArea', 'target': 'BusinessDistrict', 'source_type': 'bus', 'target_type': 'bus'},
    ]
    
    # Metro - faster but fewer locations
    metro_edges = [
        {'source': 'CentralStation', 'target': 'ShoppingMall', 'source_type': 'metro', 'target_type': 'metro'},
        {'source': 'ShoppingMall', 'target': 'BusinessDistrict', 'source_type': 'metro', 'target_type': 'metro'},
        {'source': 'BusinessDistrict', 'target': 'Airport', 'source_type': 'metro', 'target_type': 'metro'},
        {'source': 'CentralStation', 'target': 'University', 'source_type': 'metro', 'target_type': 'metro'},
        {'source': 'University', 'target': 'ResidentialArea', 'source_type': 'metro', 'target_type': 'metro'},
    ]
    
    # Walking - only nearby locations
    walking_edges = [
        {'source': 'CentralStation', 'target': 'ShoppingMall', 'source_type': 'walking', 'target_type': 'walking'},
        {'source': 'Park', 'target': 'University', 'source_type': 'walking', 'target_type': 'walking'},
        {'source': 'ShoppingMall', 'target': 'Park', 'source_type': 'walking', 'target_type': 'walking'},
        {'source': 'BusinessDistrict', 'target': 'ResidentialArea', 'source_type': 'walking', 'target_type': 'walking'},
    ]
    
    network.add_edges(bus_edges + metro_edges + walking_edges)
    
    return network


def get_dataset(name, seed=42):
    """Get a dataset by name.
    
    Args:
        name: Dataset name ('social_work', 'communication', or 'transport')
        seed: Random seed for reproducibility
        
    Returns:
        multi_layer_network: The requested network
        
    Raises:
        ValueError: If dataset name is unknown
    """
    datasets = {
        'social_work': create_social_work_network,
        'communication': create_communication_network,
        'transport': create_transport_network,
    }
    
    if name not in datasets:
        available = ', '.join(datasets.keys())
        raise ValueError(f"Unknown dataset '{name}'. Available: {available}")
    
    return datasets[name](seed=seed)
