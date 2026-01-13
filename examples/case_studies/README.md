# Py3plex Case Studies

This directory contains **complete, end-to-end workflows** demonstrating py3plex capabilities across different domains. Each case study is fully executable and follows a standard pipeline:

1. **Data Import** - Construct or load domain-specific networks
2. **Basic Stats** - Compute network properties and distributions
3. **Analysis Pipeline** - Apply 2-3 analysis steps (centrality → community detection → interpretation)
4. **Visualization** - Generate domain-relevant plots with interpretation

---

## Available Case Studies

### 1. Biological Networks
**File:** `biological_networks.py`  
**Domain:** Biology / Bioinformatics  
**Difficulty:** Intermediate

Analyzes a protein-gene-disease multilayer network demonstrating how:
- Protein interactions connect to genetic regulation
- Gene variations manifest as diseases
- Hub nodes (like TP53) are potential drug targets
- Communities reveal functional biological modules

**Layers:**
- `protein`: Protein-protein interactions (PPI)
- `gene`: Gene regulatory network
- `disease`: Disease-gene associations

**Key Techniques:**
- Multi-layer centrality analysis
- Cross-layer community detection
- Biological pathway interpretation

**Run:**
```bash
python examples/case_studies/biological_networks.py
```

---

### 2. Social Networks
**File:** `social_networks.py`  
**Domain:** Social Networks / Communication  
**Difficulty:** Beginner

Analyzes user behavior across multiple social media platforms:
- Identifies cross-platform influencers
- Detects social communities that span platforms
- Compares platform-specific communication patterns

**Layers:**
- `facebook`: Friend connections (dense, reciprocal)
- `twitter`: Follower network (sparse, broadcast)
- `linkedin`: Professional connections (moderate density)

**Key Techniques:**
- Influence metrics (PageRank, betweenness)
- Cross-platform community detection
- Platform comparison analysis

**Run:**
```bash
python examples/case_studies/social_networks.py
```

---

### 3. Transportation Networks
**File:** `transportation_networks.py`  
**Domain:** Transportation / Urban Planning  
**Difficulty:** Intermediate

Analyzes multi-modal urban transportation:
- Identifies critical transfer hubs
- Computes accessibility metrics
- Detects service zones for planning

**Layers:**
- `bus`: Dense coverage, many stops
- `metro`: Fast backbone, fewer stops
- `bike`: Short-distance, recreational

**Key Techniques:**
- Accessibility analysis (betweenness, closeness)
- Transfer hub identification
- Service zone detection
- Urban planning insights

**Run:**
```bash
python examples/case_studies/transportation_networks.py
```

---

## Case Study Structure

All case studies follow this template:

```python
# Step 1: Data Import
def create_network():
    """Build domain-specific multilayer network"""
    network = multinet.multi_layer_network()
    # Add edges for each layer
    return network

# Step 2: Basic Stats
def compute_basic_stats(network):
    """Display network statistics per layer"""
    network.basic_stats()
    # Use DSL for layer-specific metrics

# Step 3: Analysis Pipeline
def run_analysis_pipeline(network):
    """2-3 analysis steps specific to domain"""
    # e.g., centrality → communities → hubs
    return results

# Step 4: Visualization & Interpretation
def visualize_and_interpret(network, results):
    """Generate plots and interpret findings"""
    # Create 2x2 subplot grid
    # Add domain-specific interpretation
```

---

## What Makes These Different from Examples?

| Aspect | Examples (`examples/`) | Case Studies (`case_studies/`) |
|--------|----------------------|-------------------------------|
| **Scope** | Single feature demo | Complete workflow |
| **Length** | 50-150 lines | 200-400 lines |
| **Structure** | Ad-hoc | Standardized pipeline |
| **Domain** | Generic | Domain-specific |
| **Interpretation** | None/minimal | Extensive domain insights |
| **Use Case** | Learn a feature | Adapt for your data |

---

## Using These Case Studies

### As Templates

Each case study is designed to be **adapted** to your own data:

1. Replace the `create_network()` function with your data loading
2. Keep the analysis pipeline structure
3. Modify interpretation based on your domain
4. Adjust visualizations to highlight your findings

### As Learning Resources

Read the code to understand:
- How to structure a complete analysis
- Which metrics are relevant for different domains
- How to interpret multilayer network results
- Best practices for visualization

### Running Locally

All case studies are self-contained:

```bash
cd examples/case_studies
python biological_networks.py
python social_networks.py
python transportation_networks.py
```

Output:
- Console logs with statistics and findings
- Visualizations saved to `/tmp/*.png`

---

## Adapting to Your Data

### Example: Biological Networks → Your PPI Data

```python
def create_network():
    """Load your own PPI data"""
    network = multinet.multi_layer_network()
    
    # Load from file
    import pandas as pd
    ppi_data = pd.read_csv('my_ppi_interactions.csv')
    
    # Convert to edges
    edges = []
    for _, row in ppi_data.iterrows():
        edges.append([
            row['protein_a'], 'ppi',
            row['protein_b'], 'ppi', 
            row['confidence']
        ])
    
    network.add_edges(edges, input_type="list")
    return network

# Rest of the pipeline stays the same!
```

---

## Contributing Case Studies

Want to add a case study? Follow these guidelines:

1. **Choose a clear domain** (e.g., Neuroscience, Finance, Ecology)
2. **Follow the 4-step structure** (Import → Stats → Pipeline → Viz)
3. **Use synthetic data** (or public datasets with clear license)
4. **Add extensive interpretation** (domain-specific insights)
5. **Test that it runs** (no missing dependencies)
6. **Document difficulty** (Beginner/Intermediate/Advanced)

Submit via pull request to https://github.com/SkBlaz/py3plex

---

## Metadata

Each case study includes metadata in the docstring:

```python
"""
Case Study: Your Title
======================

Domain: Your Domain
Difficulty: Beginner / Intermediate / Advanced
Dataset: Description of data

Brief description of what the case study demonstrates.
"""
```

This helps users find relevant case studies quickly.

---

## Related Documentation

- [Examples Directory](../README.md) - Single-feature demonstrations
- [10-Minute Tutorial](../../docfiles/getting_started/tutorial_10min.rst) - Quick start
- [DSL Guide](../../docfiles/how-to/query_with_dsl.rst) - Query language reference
- [Book](../../book/) - Comprehensive theoretical background

---

## Support

- **Issues:** https://github.com/SkBlaz/py3plex/issues
- **Discussions:** https://github.com/SkBlaz/py3plex/discussions
- **Email:** blaz.skrlj@ijs.si
