# Multilayer Network Corner Case Test Findings

This document summarizes the corner cases identified and tested for the `multi_layer_network` class.

## Test Execution Summary

**Total Tests:** 49  
**Passing:** 38  
**Failing:** 4  
**Errors:** 7  

## Identified Bugs

### Critical Bugs (Errors - 7)

#### 1. Edge Operations Without Layer Information
- **Test:** `test_add_edge_without_layers`, `test_add_duplicate_edges`
- **Location:** `py3plex/core/multinet.py:810` in `_generic_edge_dict_manipulator`
- **Issue:** `KeyError` when trying to delete `target_type` or `source_type` keys that don't exist
- **Scenario:** Adding edges without specifying layer information should use dummy layer
- **Root Cause:** Code tries to delete keys without checking if they exist

```python
# Fails when source_type/target_type are missing
del edge_dict["target_type"]
del edge_dict["source_type"]
```

#### 2. Node Operations Without Type Field
- **Test:** `test_add_single_node_without_layer`
- **Location:** `py3plex/core/multinet.py:890` in `_generic_node_dict_manipulator`
- **Issue:** `KeyError: 'type'` when adding node without type field
- **Scenario:** Adding a node without layer information should use dummy layer
- **Root Cause:** Code tries to delete 'type' key that doesn't exist

```python
# Fails when 'type' key is missing
del node_dict["type"]
```

#### 3. Empty Node List Handling
- **Test:** `test_add_empty_node_list`
- **Location:** `py3plex/core/multinet.py:906` in `_generic_node_dict_manipulator`
- **Issue:** `UnboundLocalError` when processing empty list
- **Scenario:** Adding an empty list of nodes should be a no-op
- **Root Cause:** Variable scope issue in loop handling

#### 4. Dictionary Mutation in Duplicate Operations
- **Test:** `test_add_duplicate_nodes`
- **Location:** `py3plex/core/multinet.py:883` in `_generic_node_dict_manipulator`
- **Issue:** `KeyError: 'source'` on second add attempt
- **Scenario:** Adding same node twice should be idempotent
- **Root Cause:** Dictionary gets mutated (keys deleted) on first call, second call fails

#### 5. Empty Network Layer Splitting
- **Test:** `test_split_to_layers_on_empty_network`
- **Location:** `py3plex/core/converters.py:244` in `prepare_for_parsing`
- **Issue:** `ValueError` when unpacking empty dictionary
- **Scenario:** Splitting empty network to layers should return empty structures
- **Root Cause:** Code assumes network has at least one layer

```python
# Fails on empty dictionary
names, networks = zip(*networks.items())
```

#### 6. Remove Operations Missing Keys
- **Test:** `test_remove_existing_node`
- **Location:** `py3plex/core/multinet.py:883` in `_generic_node_dict_manipulator`
- **Issue:** `KeyError: 'source'` when removing node
- **Scenario:** Removing existing node should work
- **Root Cause:** Same mutation issue as addition - keys already deleted from previous operations

### Logic Issues (Failures - 4)

#### 7. Incorrect Layer Counting
- **Test:** `test_get_num_layers_multiple_layers`
- **Expected:** 3 layers
- **Actual:** 1 layer
- **Issue:** When adding nodes `[{source: "node1", type: "layer1"}, {source: "node2", type: "layer2"}, {source: "node3", type: "layer3"}]`, only 1 layer is counted
- **Root Cause:** Only the last node's type is considered, or nodes aren't being added correctly

#### 8. Incorrect Unique Node Counting
- **Test:** `test_get_num_nodes_same_node_different_layers`
- **Expected:** 2 unique nodes (node1 and node2)
- **Actual:** 1 unique node
- **Issue:** When adding same node to different layers, node count is wrong
- **Root Cause:** Related to issue #7 - nodes may not be added correctly

#### 9. Multiplex Coupling Not Working
- **Test:** `test_multiplex_single_node_multiple_layers`
- **Expected:** Coupling edges between layers for same node
- **Actual:** No coupling edges created
- **Issue:** Multiplex network should automatically create inter-layer edges
- **Root Cause:** `_couple_all_edges()` may not work correctly with manually added nodes

#### 10. Multiple Node Addition Fails
- **Test:** `test_add_multiple_nodes`
- **Expected:** 3 nodes added
- **Actual:** Only 1 node added
- **Issue:** When passing list of node dictionaries, only one is actually added
- **Root Cause:** Loop or iteration issue in `_generic_node_dict_manipulator`

## Corner Cases Successfully Handled

### Initialization (11/11 passing)
- ✅ Empty network initialization (multilayer, multiplex)
- ✅ Custom parameters (verbose, directed, dummy_layer, label_delimiter, coupling_weight)
- ✅ Zero and negative coupling weights
- ✅ Directed vs undirected networks

### Empty Network Operations (2/3 passing)
- ✅ Getting nodes/edges from empty network
- ❌ Splitting empty network to layers

### Edge Operations (6/8 passing)
- ✅ Single edge addition with layers
- ✅ Multiple edges
- ✅ Empty edge list
- ✅ Self-loops
- ✅ Inter-layer edges
- ✅ List format edges
- ❌ Edges without layer info
- ❌ Duplicate edges

### Node Operations (2/6 passing)
- ✅ Single node with layer
- ❌ Node without layer
- ❌ Multiple nodes
- ❌ Empty node list
- ❌ Duplicate nodes

### Query Operations (3/3 passing)
- ✅ Get neighbors from empty network (handled gracefully)
- ✅ Get neighbors of non-existent node (handled gracefully)
- ✅ Get neighbors of existing node

### Network Type Specific (2/3 passing)
- ✅ Multiplex empty coupling
- ✅ Multiplex single node coupling
- ❌ Multiplex single node multiple layers

### Layer Operations (5/7 passing)
- ✅ Layer counting on empty network
- ✅ Single layer counting
- ❌ Multiple layer counting
- ✅ Node counting on empty network
- ❌ Unique node counting across layers

### Invalid Inputs (3/3 passing)
- ✅ Invalid input type raises exception
- ✅ Malformed dictionaries handled
- ✅ Malformed lists handled

### Network Loading (4/4 passing)
- ✅ None file path handled
- ✅ Non-existent file handled
- ✅ Empty NetworkX graph loaded
- ✅ NetworkX graph with data loaded

### Network Conversion (2/2 passing)
- ✅ Empty network to JSON
- ✅ Network with data to JSON

### Remove Operations (1/3 passing)
- ✅ Remove from empty network handled
- ✅ Remove non-existent edge handled
- ❌ Remove existing node

### Subnetwork Operations (3/3 passing)
- ✅ Empty list extraction
- ✅ Single layer extraction
- ✅ Non-existent layer extraction

## Recommendations

1. **Fix Dictionary Mutation**: Don't delete keys from input dictionaries - work with copies
2. **Add Existence Checks**: Check if keys exist before trying to delete them
3. **Handle Empty Collections**: Add guards for empty lists/dicts in iteration
4. **Fix Node Addition**: Debug why only one node is added from a list
5. **Fix Layer Counting**: Ensure all nodes are actually added to the network
6. **Test Multiplex Coupling**: Verify `_couple_all_edges()` works with manually added nodes

## Test File Location

`tests/test_multilayer_cornercases.py`

## How to Run Tests

```bash
# Install dependencies
pip install networkx numpy scipy pandas

# Install py3plex in development mode
pip install -e .

# Run the corner case tests
python tests/test_multilayer_cornercases.py
```
