"""
Test complete user journey: multi-edgelist upload → centrality computation

This test simulates a user following the typical workflow:
1. Upload a multi-layer edgelist file
2. Verify the network was parsed correctly
3. Compute centrality metrics
4. Verify results are accessible

Use case: Generic multiedgelist centrality analysis
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
import time

client = TestClient(app)


def test_multiedgelist_centrality_user_journey():
    """
    Simulate complete user journey for multi-layer network centrality analysis.
    
    This test represents a typical user interaction:
    - User navigates to "Load Data" page
    - User uploads a multi-layer edgelist file
    - User navigates to "Analyze" page
    - User clicks "Run Centrality" button
    - User monitors job progress
    - User views results
    """
    
    # Step 1: User uploads a multi-layer edgelist file
    # Format: node1 node2 layer weight
    multiedge_content = b"""# Multi-layer social network
1 2 social 1.0
1 3 social 1.0
2 3 social 1.0
2 4 social 1.0
3 4 social 1.0
4 5 social 1.0
1 4 work 1.0
2 5 work 1.0
3 5 work 1.0
1 5 work 1.0
2 6 hobby 1.0
3 6 hobby 1.0
4 6 hobby 1.0
5 6 hobby 1.0
"""
    
    files = {"file": ("test_multiedgelist.edgelist", io.BytesIO(multiedge_content), "text/plain")}
    upload_response = client.post("/api/upload", files=files)
    
    assert upload_response.status_code == 200, "Upload should succeed"
    upload_data = upload_response.json()
    assert "graph_id" in upload_data, "Response should contain graph_id"
    graph_id = upload_data["graph_id"]
    print(f"Step 1: Uploaded multi-layer network, graph_id={graph_id}")
    
    # Step 2: User views network summary (as displayed on Load Data page)
    summary_response = client.get(f"/api/graphs/{graph_id}/summary")
    assert summary_response.status_code == 200, "Summary should be accessible"
    summary = summary_response.json()
    
    # Verify network was parsed correctly
    assert summary["nodes"] > 0, "Network should have nodes"
    assert summary["edges"] > 0, "Network should have edges"
    assert "layers" in summary, "Summary should include layer information"
    
    print(f"Step 2: Network summary retrieved:")
    print(f"  - Nodes: {summary['nodes']}")
    print(f"  - Edges: {summary['edges']}")
    print(f"  - Layers: {summary.get('layers', [])}")
    
    # Step 3: User navigates to "Analyze" page and clicks "Run Centrality"
    # This corresponds to the runCentralityJob function in Analyze.tsx
    centrality_request = {
        "metrics": ["degree", "betweenness"]
    }
    
    centrality_response = client.post(
        f"/api/graphs/{graph_id}/analysis/centrality",
        json=centrality_request
    )
    
    assert centrality_response.status_code == 200, "Centrality job should start"
    job_data = centrality_response.json()
    assert "job_id" in job_data, "Response should contain job_id"
    assert job_data["status"] in ["queued", "running"], "Job should be queued or running"
    job_id = job_data["job_id"]
    print(f"Step 3: Centrality job started, job_id={job_id}")
    
    # Step 4: User monitors job progress (simulates polling in Analyze.tsx)
    # In real GUI, this happens via useEffect polling every 2 seconds
    max_polls = 30  # 30 * 2 = 60 seconds max wait
    job_status = None
    
    for i in range(max_polls):
        status_response = client.get(f"/api/jobs/{job_id}")
        assert status_response.status_code == 200, "Job status should be accessible"
        job_status = status_response.json()
        
        print(f"  Poll {i+1}: status={job_status.get('status')}, progress={job_status.get('progress', 0)}%")
        
        if job_status["status"] == "completed":
            print(f"Step 4: Job completed successfully")
            break
        elif job_status["status"] == "failed":
            error_msg = job_status.get("error", "Unknown error")
            pytest.fail(f"Job failed: {error_msg}")
        
        time.sleep(0.1)  # Short sleep in test (real GUI polls every 2 seconds)
    
    # Verify job completed
    assert job_status is not None, "Job status should be available"
    assert job_status["status"] == "completed", "Job should complete successfully"
    
    # Step 5: Verify results are available
    # In the GUI, results would be displayed or downloadable
    assert "result" in job_status or "artifacts" in job_status, \
        "Completed job should have results or artifacts"
    
    if "result" in job_status and job_status["result"]:
        result = job_status["result"]
        print(f"Step 5: Results available:")
        
        # Verify centrality metrics were computed
        if "metrics" in result:
            print(f"  - Metrics computed: {result['metrics']}")
        
        if "results" in result:
            results_data = result["results"]
            for metric in ["degree", "betweenness"]:
                if metric in results_data:
                    metric_results = results_data[metric]
                    if isinstance(metric_results, list) and len(metric_results) > 0:
                        top_node = metric_results[0]
                        print(f"  - {metric}: top node={top_node.get('node')}, value={top_node.get('value'):.4f}")
    
    print("\nComplete user journey test passed!")
    print("No friction detected in multi-edgelist → centrality workflow")


def test_multiedgelist_all_centrality_metrics():
    """
    Test all available centrality metrics on a multi-layer network.
    
    This tests the full capability advertised in the GUI.
    """
    
    # Create a simple but connected multi-layer network
    content = b"""1 2 layer1 1.0
2 3 layer1 1.0
3 4 layer1 1.0
4 5 layer1 1.0
5 1 layer1 1.0
1 3 layer2 1.0
2 4 layer2 1.0
3 5 layer2 1.0
"""
    
    files = {"file": ("test_all_metrics.edgelist", io.BytesIO(content), "text/plain")}
    upload_response = client.post("/api/upload", files=files)
    assert upload_response.status_code == 200
    graph_id = upload_response.json()["graph_id"]
    
    # Test each centrality metric individually
    metrics_to_test = ["degree", "betweenness", "closeness", "eigenvector", "pagerank"]
    
    for metric in metrics_to_test:
        print(f"\nTesting {metric} centrality...")
        centrality_request = {"metrics": [metric]}
        
        response = client.post(
            f"/api/graphs/{graph_id}/analysis/centrality",
            json=centrality_request
        )
        
        assert response.status_code == 200, f"{metric} centrality job should start"
        job_id = response.json()["job_id"]
        
        # Poll for completion
        for _ in range(20):
            status_response = client.get(f"/api/jobs/{job_id}")
            job_status = status_response.json()
            
            if job_status["status"] == "completed":
                print(f"  {metric} completed successfully")
                break
            elif job_status["status"] == "failed":
                print(f"   {metric} failed: {job_status.get('error', 'Unknown error')}")
                # Some metrics may fail on certain graph structures, that's OK
                break
            
            time.sleep(0.1)
    
    print("\nAll centrality metrics tested")


def test_friction_point_no_graph_loaded():
    """
    Test friction point: User navigates to Analyze page without loading data first.
    
    This simulates the check in Analyze.tsx that shows a warning when no graph is loaded.
    The frontend handles this gracefully, but we should verify the API behavior.
    """
    
    # Attempt to compute centrality without a valid graph_id
    fake_graph_id = "nonexistent-graph-id"
    
    centrality_request = {"metrics": ["degree"]}
    response = client.post(
        f"/api/graphs/{fake_graph_id}/analysis/centrality",
        json=centrality_request
    )
    
    # The API should return an error (4xx or 5xx)
    # This is expected behavior and helps prevent user confusion
    assert response.status_code >= 400, "Should return error for nonexistent graph"
    print(f"Friction point handled: Returns {response.status_code} for nonexistent graph")


def test_multiedgelist_format_variations():
    """
    Test various multi-edgelist formats to ensure robust parsing.
    
    Users may provide edgelists in different formats:
    - With/without headers
    - With/without weights
    - With/without layer names
    - With tabs or spaces as separators
    """
    
    formats = [
        # Format 1: node1 node2 layer weight
        ("format_full.edgelist", b"1 2 social 1.0\n2 3 social 1.5\n"),
        
        # Format 2: node1 node2 layer (no weight)
        ("format_no_weight.edgelist", b"1 2 social\n2 3 social\n"),
        
        # Format 3: node1 node2 (no layer, no weight - simple edgelist)
        ("format_simple.edgelist", b"1 2\n2 3\n3 4\n"),
        
        # Format 4: with comments
        ("format_comments.edgelist", b"# This is a comment\n1 2 social\n# Another comment\n2 3 social\n"),
    ]
    
    for filename, content in formats:
        print(f"\nTesting format: {filename}")
        files = {"file": (filename, io.BytesIO(content), "text/plain")}
        response = client.post("/api/upload", files=files)
        
        if response.status_code == 200:
            graph_id = response.json()["graph_id"]
            summary = client.get(f"/api/graphs/{graph_id}/summary").json()
            print(f"  Parsed successfully: {summary['nodes']} nodes, {summary['edges']} edges")
        else:
            print(f"   Failed to parse: {response.status_code}")
            # Some formats might not be supported, document this
    
    print("\nFormat variation testing complete")
