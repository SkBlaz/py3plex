# Py3plex Jupyter Notebooks

This directory contains interactive Jupyter notebooks for learning py3plex. Each notebook is self-contained and can be run directly in Google Colab without any local installation.

## Available Notebooks

### 1. 10-Minute Tutorial
**File:** `tutorial_10min.ipynb`  
**Colab:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SkBlaz/py3plex/blob/main/notebooks/tutorial_10min.ipynb)

A quick introduction to py3plex covering:
- Creating multilayer networks
- Computing statistics
- Querying with DSL
- Detecting communities
- Visualizing networks

**Perfect for:** First-time users, quick overview

---

### 2. Query with DSL
**File:** `query_with_dsl.ipynb`  
**Colab:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SkBlaz/py3plex/blob/main/notebooks/query_with_dsl.ipynb)

Deep dive into py3plex's SQL-like query language:
- String DSL syntax
- Builder API (Q, L)
- Layer algebra
- Computing metrics
- Complex filtering
- Export options

**Perfect for:** Users who want to master the DSL

---

### 3. Simulate Dynamics
**File:** `simulate_dynamics.ipynb`  
**Colab:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SkBlaz/py3plex/blob/main/notebooks/simulate_dynamics.ipynb)

Learn to simulate dynamical processes:
- SIR epidemic models
- SIS dynamics
- Parameter exploration
- Epidemic curves
- Layer-specific analysis

**Perfect for:** Researchers studying spreading processes

---

### 4. Community Detection
**File:** `community_detection.ipynb`  
**Colab:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SkBlaz/py3plex/blob/main/notebooks/community_detection.ipynb)

Detect and analyze communities:
- Louvain algorithm
- Multilayer vs single-layer
- Community visualization
- Layer-specific communities
- Community metrics

**Perfect for:** Users analyzing network structure

---

## Running Notebooks Locally

### Option 1: Jupyter Notebook

```bash
# Install Jupyter
pip install jupyter

# Navigate to notebooks directory
cd notebooks

# Start Jupyter
jupyter notebook
```

### Option 2: JupyterLab

```bash
# Install JupyterLab
pip install jupyterlab

# Navigate to notebooks directory
cd notebooks

# Start JupyterLab
jupyter lab
```

### Option 3: VS Code

1. Install the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
2. Open any `.ipynb` file
3. Click "Run All" or run cells individually

---

## Google Colab Tips

**Installation:** The first cell in each notebook installs py3plex automatically:
```python
!pip install py3plex -q
```

**GPU/TPU:** Not needed for py3plex (CPU is sufficient)

**Saving your work:** 
- File → Save a copy in Drive (creates a copy you can edit)
- File → Download → Download .ipynb

**Running time:** Most notebooks complete in 2-5 minutes

---

## Prerequisites

All notebooks are self-contained and include:
- Installation commands
- Sample data generation
- Complete working examples
- Expected outputs

**No prior knowledge required!** Just click a Colab badge and start learning.

---

## Contributing

To contribute a new notebook:

1. Create a `.ipynb` file following the existing style
2. Include installation cell at the top
3. Use markdown for explanations
4. Include visualizations where appropriate
5. Test in Colab before submitting
6. Add entry to this README

---

## Related Documentation

- [Full Documentation](https://skblaz.github.io/py3plex/)
- [Example Scripts](../examples/)
- [API Reference](https://skblaz.github.io/py3plex/reference/api_index.html)
- [Book (PDF)](https://skblaz.github.io/py3plex/py3plex_book.pdf)

---

## Support

- **Issues:** https://github.com/SkBlaz/py3plex/issues
- **Discussions:** https://github.com/SkBlaz/py3plex/discussions
- **Email:** blaz.skrlj@ijs.si
