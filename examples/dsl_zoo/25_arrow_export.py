# Arrow export
from py3plex.core import multinet
from py3plex.dsl import Q, L

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': f'N{i}', 'type': 'social'} for i in range(15)])
net.add_edges([
    {'source': f'N{i}', 'target': f'N{(i+1)%15}', 'source_type': 'social', 'target_type': 'social'}
    for i in range(15)
])

result = (
    Q.nodes()
    .from_layers(L["*"])
    .compute("pagerank")
    .execute(net)
)

# Export to Arrow format
try:
    arrow_table = result.to_arrow()
    print("Arrow table exported successfully!")
    print(f"Schema: {arrow_table.schema}")
    print(f"Rows: {arrow_table.num_rows}")
    
    # Optionally save to file
    import pyarrow.parquet as pq
    output_path = "/home/runner/work/py3plex/py3plex/examples/dsl_zoo/out_pagerank.parquet"
    pq.write_table(arrow_table, output_path)
    print(f"Saved to: {output_path}")
except ImportError:
    print("PyArrow not installed, showing pandas instead:")
    print(result.to_pandas().head())
except Exception as e:
    print(f"Export failed: {e}")
    print("Showing pandas output instead:")
    print(result.to_pandas().head())
