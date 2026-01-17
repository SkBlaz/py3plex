"""Tests for cost model and execution planning.

Tests cost estimation, budget enforcement, and execution planning.
"""

import pytest
import time

from py3plex.dsl import Q
from py3plex.dsl.program import (
    GraphProgram,
    Cost,
    CostModel,
    CostObjective,
    GraphStats,
    ExecutionContext,
    ExecutionPlan,
    BudgetExceededError,
    create_execution_plan,
    execute_program,
    estimate_program_cost,
    parse_time_budget,
    format_time_estimate,
    format_memory_estimate,
)


@pytest.fixture
def small_network():
    """Create a small multilayer network for testing."""
    from py3plex.core import multinet
    
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = []
    for i in range(100):
        nodes.append({"source": f"n{i}", "type": "social"})
        nodes.append({"source": f"n{i}", "type": "work"})
    net.add_nodes(nodes)
    
    # Add edges
    edges = []
    for i in range(90):
        edges.append({
            "source": f"n{i}",
            "target": f"n{i+1}",
            "source_type": "social",
            "target_type": "social",
        })
        edges.append({
            "source": f"n{i}",
            "target": f"n{i+1}",
            "source_type": "work",
            "target_type": "work",
        })
    net.add_edges(edges)
    
    return net


@pytest.fixture
def medium_network():
    """Create a medium multilayer network for testing."""
    from py3plex.core import multinet
    
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = []
    for i in range(1000):
        nodes.append({"source": f"n{i}", "type": "social"})
        if i % 2 == 0:
            nodes.append({"source": f"n{i}", "type": "work"})
    net.add_nodes(nodes)
    
    # Add edges
    edges = []
    for i in range(900):
        edges.append({
            "source": f"n{i}",
            "target": f"n{i+1}",
            "source_type": "social",
            "target_type": "social",
        })
    
    for i in range(0, 500, 2):
        edges.append({
            "source": f"n{i}",
            "target": f"n{i+2}",
            "source_type": "work",
            "target_type": "work",
        })
    net.add_edges(edges)
    
    return net


class TestGraphStats:
    """Test GraphStats extraction and usage."""
    
    def test_from_network_basic(self, small_network):
        """Test extracting stats from a network."""
        stats = GraphStats.from_network(small_network)
        
        assert stats.num_nodes > 0
        assert stats.num_edges > 0
        assert stats.num_layers >= 1
        assert stats.avg_degree >= 0.0
    
    def test_manual_creation(self):
        """Test creating stats manually."""
        stats = GraphStats(
            num_nodes=1000,
            num_edges=5000,
            num_layers=3,
            avg_degree=5.0,
            max_degree=50,
        )
        
        assert stats.num_nodes == 1000
        assert stats.num_edges == 5000
        assert stats.num_layers == 3
        assert stats.avg_degree == 5.0
        assert stats.max_degree == 50


class TestCost:
    """Test Cost dataclass and operations."""
    
    def test_cost_creation(self):
        """Test creating a cost estimate."""
        cost = Cost(
            time_complexity="O(V + E)",
            time_estimate_seconds=1.5,
            memory_estimate_bytes=1024 * 1024,
            parallelizable=True,
            constants={"test": 1.0},
            confidence=0.9,
        )
        
        assert cost.time_complexity == "O(V + E)"
        assert cost.time_estimate_seconds == 1.5
        assert cost.memory_estimate_bytes == 1024 * 1024
        assert cost.parallelizable is True
        assert cost.confidence == 0.9
    
    def test_cost_addition(self):
        """Test adding costs together."""
        cost1 = Cost(
            time_complexity="O(V)",
            time_estimate_seconds=1.0,
            memory_estimate_bytes=1000,
            parallelizable=True,
        )
        
        cost2 = Cost(
            time_complexity="O(E)",
            time_estimate_seconds=2.0,
            memory_estimate_bytes=2000,
            parallelizable=True,
        )
        
        total = cost1 + cost2
        
        assert total.time_estimate_seconds == 3.0
        assert total.memory_estimate_bytes == 2000  # Max
        assert total.parallelizable is True
    
    def test_cost_scaling(self):
        """Test scaling a cost."""
        cost = Cost(
            time_complexity="O(V)",
            time_estimate_seconds=1.0,
            memory_estimate_bytes=1000,
        )
        
        scaled = cost.scale(2.5)
        
        assert scaled.time_estimate_seconds == 2.5
        assert scaled.memory_estimate_bytes == 2500


class TestCostModel:
    """Test cost estimation for operators."""
    
    def test_degree_cost(self):
        """Test cost estimation for degree centrality."""
        model = CostModel()
        stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=2)
        
        cost = model.estimate_operator_cost("degree", None, stats)
        
        assert cost.time_complexity == "O(E)"
        assert cost.time_estimate_seconds > 0
        assert cost.memory_estimate_bytes > 0
    
    def test_betweenness_cost(self):
        """Test cost estimation for betweenness centrality."""
        model = CostModel()
        stats = GraphStats(num_nodes=100, num_edges=500, num_layers=2)
        
        cost = model.estimate_operator_cost("betweenness_centrality", None, stats)
        
        assert "V" in cost.time_complexity and "E" in cost.time_complexity
        assert cost.time_estimate_seconds > 0
        # Betweenness should be more expensive than degree
        degree_cost = model.estimate_operator_cost("degree", None, stats)
        assert cost.time_estimate_seconds > degree_cost.time_estimate_seconds
    
    def test_pagerank_cost(self):
        """Test cost estimation for PageRank."""
        model = CostModel()
        stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=1)
        
        cost = model.estimate_operator_cost("pagerank", None, stats)
        
        assert "iterations" in cost.time_complexity.lower() or "E" in cost.time_complexity
        assert cost.time_estimate_seconds > 0
        assert "iterations" in cost.constants
    
    def test_clustering_cost(self):
        """Test cost estimation for clustering coefficient."""
        model = CostModel()
        stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=1)
        
        cost = model.estimate_operator_cost("clustering", None, stats)
        
        assert cost.time_estimate_seconds > 0
        assert cost.memory_estimate_bytes > 0
    
    def test_unknown_operator_cost(self):
        """Test default cost for unknown operators."""
        model = CostModel()
        stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=1)
        
        cost = model.estimate_operator_cost("unknown_measure", None, stats)
        
        assert cost.time_complexity == "O(V + E)"
        assert cost.time_estimate_seconds > 0
        assert cost.confidence < 0.8  # Lower confidence for unknown
    
    def test_program_cost_simple(self, small_network):
        """Test cost estimation for a simple program."""
        model = CostModel()
        stats = GraphStats.from_network(small_network)
        
        program = GraphProgram.from_ast(
            Q.nodes().compute("degree").to_ast()
        )
        
        cost = model.estimate_program_cost(program, stats)
        
        assert cost.time_estimate_seconds > 0
        assert cost.memory_estimate_bytes > 0
    
    def test_program_cost_complex(self, small_network):
        """Test cost estimation for a complex program."""
        model = CostModel()
        stats = GraphStats.from_network(small_network)
        
        program = GraphProgram.from_ast(
            Q.nodes()
            .compute("degree")
            .compute("betweenness_centrality")
            .where(lambda n: n["degree"] > 2)
            .order_by("degree")
            .to_ast()
        )
        
        cost = model.estimate_program_cost(program, stats)
        
        assert cost.time_estimate_seconds > 0
        # Should be more expensive than simple program
        simple_program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        simple_cost = model.estimate_program_cost(simple_program, stats)
        assert cost.time_estimate_seconds > simple_cost.time_estimate_seconds


class TestTimeParsing:
    """Test time budget parsing and formatting."""
    
    def test_parse_seconds(self):
        """Test parsing seconds."""
        assert parse_time_budget("30") == 30.0
        assert parse_time_budget("30s") == 30.0
        assert parse_time_budget("30.5s") == 30.5
    
    def test_parse_minutes(self):
        """Test parsing minutes."""
        assert parse_time_budget("5m") == 300.0
        assert parse_time_budget("2.5m") == 150.0
    
    def test_parse_hours(self):
        """Test parsing hours."""
        assert parse_time_budget("1h") == 3600.0
        assert parse_time_budget("0.5h") == 1800.0
    
    def test_parse_float(self):
        """Test parsing float directly."""
        assert parse_time_budget(30.0) == 30.0
        assert parse_time_budget(123.45) == 123.45
    
    def test_format_seconds(self):
        """Test formatting seconds."""
        assert "s" in format_time_estimate(45.5)
    
    def test_format_minutes(self):
        """Test formatting minutes."""
        result = format_time_estimate(125.0)
        assert "m" in result
    
    def test_format_hours(self):
        """Test formatting hours."""
        result = format_time_estimate(7200.0)
        assert "h" in result


class TestMemoryFormatting:
    """Test memory formatting."""
    
    def test_format_bytes(self):
        """Test formatting bytes."""
        assert "B" in format_memory_estimate(512)
    
    def test_format_kb(self):
        """Test formatting kilobytes."""
        result = format_memory_estimate(2048)
        assert "KB" in result
    
    def test_format_mb(self):
        """Test formatting megabytes."""
        result = format_memory_estimate(1048576)
        assert "MB" in result
    
    def test_format_gb(self):
        """Test formatting gigabytes."""
        result = format_memory_estimate(1073741824)
        assert "GB" in result


class TestExecutionContext:
    """Test execution context creation and usage."""
    
    def test_default_context(self):
        """Test creating default context."""
        context = ExecutionContext()
        
        assert context.time_budget is None
        assert context.memory_budget is None
        assert context.n_jobs == 1
        assert context.cache_policy == "auto"
    
    def test_context_with_budget(self):
        """Test creating context with time budget."""
        context = ExecutionContext.create(time_budget="30s", n_jobs=4)
        
        assert context.time_budget == 30.0
        assert context.n_jobs == 4
    
    def test_context_with_memory_budget(self):
        """Test creating context with memory budget."""
        context = ExecutionContext(
            time_budget=60.0,
            memory_budget=1024 * 1024 * 100,  # 100 MB
        )
        
        assert context.time_budget == 60.0
        assert context.memory_budget == 1024 * 1024 * 100


class TestExecutionPlan:
    """Test execution plan creation."""
    
    def test_create_plan_simple(self, small_network):
        """Test creating a simple execution plan."""
        program = GraphProgram.from_ast(
            Q.nodes().compute("degree").to_ast()
        )
        
        context = ExecutionContext()
        stats = GraphStats.from_network(small_network)
        
        plan = create_execution_plan(program, context, stats)
        
        assert len(plan.stages) > 0
        assert plan.estimated_cost.time_estimate_seconds > 0
        assert plan.estimated_cost.memory_estimate_bytes > 0
    
    def test_create_plan_complex(self, small_network):
        """Test creating a complex execution plan."""
        program = GraphProgram.from_ast(
            Q.nodes()
            .compute("degree")
            .compute("betweenness_centrality")
            .where(lambda n: n["degree"] > 2)
            .order_by("degree")
            .limit(10)
            .to_ast()
        )
        
        context = ExecutionContext(n_jobs=4)
        stats = GraphStats.from_network(small_network)
        
        plan = create_execution_plan(program, context, stats)
        
        # Should have multiple stages
        assert len(plan.stages) >= 3
        
        # Check for expected stages
        stage_ops = [s.operation for s in plan.stages]
        assert "iterate_nodes" in stage_ops
        assert any("compute_" in op for op in stage_ops)
    
    def test_plan_to_dict(self, small_network):
        """Test serializing plan to dictionary."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        context = ExecutionContext()
        stats = GraphStats.from_network(small_network)
        
        plan = create_execution_plan(program, context, stats)
        plan_dict = plan.to_dict()
        
        assert "stages" in plan_dict
        assert "estimated_cost" in plan_dict
        assert "time_estimate_formatted" in plan_dict["estimated_cost"]
    
    def test_plan_summary(self, small_network):
        """Test generating plan summary."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        context = ExecutionContext()
        stats = GraphStats.from_network(small_network)
        
        plan = create_execution_plan(program, context, stats)
        summary = plan.summary()
        
        assert isinstance(summary, str)
        assert "Execution Plan" in summary
        assert "Estimated Time" in summary


class TestBudgetEnforcement:
    """Test budget enforcement and error handling."""
    
    def test_budget_exceeded_simple(self, medium_network):
        """Test budget exceeded error for expensive operation."""
        program = GraphProgram.from_ast(
            Q.nodes().compute("betweenness_centrality").to_ast()
        )
        
        # Set very tight budget
        context = ExecutionContext.create(time_budget="0.001s")
        stats = GraphStats.from_network(medium_network)
        
        with pytest.raises(BudgetExceededError) as excinfo:
            create_execution_plan(program, context, stats)
        
        assert "exceeds budget" in str(excinfo.value).lower()
    
    def test_budget_not_exceeded(self, small_network):
        """Test that reasonable budget doesn't raise error."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        
        context = ExecutionContext.create(time_budget="10s")
        stats = GraphStats.from_network(small_network)
        
        # Should not raise
        plan = create_execution_plan(program, context, stats)
        assert plan is not None
    
    def test_budget_suggestions(self, medium_network):
        """Test that budget error includes suggestions."""
        program = GraphProgram.from_ast(
            Q.nodes().compute("betweenness_centrality").to_ast()
        )
        
        context = ExecutionContext.create(time_budget="0.001s")
        stats = GraphStats.from_network(medium_network)
        
        with pytest.raises(BudgetExceededError) as excinfo:
            create_execution_plan(program, context, stats)
        
        error = excinfo.value
        assert error.suggestions is not None
        assert len(error.suggestions) > 0


class TestProgramExecution:
    """Test program execution with budget."""
    
    def test_execute_simple(self, small_network):
        """Test executing a simple program."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        
        context = ExecutionContext(progress=False)
        result = execute_program(program, small_network, context)
        
        assert result is not None
        assert "execution_time" in result.meta
        assert "estimated_time" in result.meta
    
    def test_execute_with_budget(self, small_network):
        """Test executing with time budget."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        
        context = ExecutionContext.create(time_budget="10s", progress=False)
        result = execute_program(program, small_network, context)
        
        assert result is not None
        assert result.meta["execution_time"] < 10.0  # Should complete within budget
    
    def test_execute_explain(self, small_network):
        """Test execution with explain mode."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        
        context = ExecutionContext(explain=True, progress=False)
        result = execute_program(program, small_network, context)
        
        assert "plan" in result.meta
        assert "plan_summary" in result.meta
    
    def test_estimate_cost(self, small_network):
        """Test estimating cost without execution."""
        program = GraphProgram.from_ast(
            Q.nodes().compute("degree").compute("betweenness_centrality").to_ast()
        )
        
        cost = estimate_program_cost(program, small_network)
        
        assert cost.time_estimate_seconds > 0
        assert cost.memory_estimate_bytes > 0


class TestParallelization:
    """Test parallelization strategies."""
    
    def test_parallel_context(self, small_network):
        """Test creating plan with parallelization."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        
        context = ExecutionContext(n_jobs=4, progress=False)
        stats = GraphStats.from_network(small_network)
        
        plan = create_execution_plan(program, context, stats)
        
        # Should have parallelization strategy
        if plan.estimated_cost.parallelizable:
            assert "n_jobs" in plan.parallelization_strategy
            assert plan.parallelization_strategy["n_jobs"] == 4
    
    def test_parallel_speedup(self, small_network):
        """Test that parallel execution reduces estimated time."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        stats = GraphStats.from_network(small_network)
        
        # Sequential
        context_seq = ExecutionContext(n_jobs=1)
        plan_seq = create_execution_plan(program, context_seq, stats)
        
        # Parallel
        context_par = ExecutionContext(n_jobs=4)
        plan_par = create_execution_plan(program, context_par, stats)
        
        # Parallel should be faster (if parallelizable)
        if plan_par.estimated_cost.parallelizable:
            assert (
                plan_par.estimated_cost.time_estimate_seconds <=
                plan_seq.estimated_cost.time_estimate_seconds
            )


class TestCostAccuracy:
    """Test cost estimation accuracy (integration tests)."""
    
    @pytest.mark.slow
    def test_degree_cost_accuracy(self, small_network):
        """Test that degree cost estimate is reasonably accurate."""
        program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
        
        # Estimate
        cost = estimate_program_cost(program, small_network)
        estimated_time = cost.time_estimate_seconds
        
        # Execute
        context = ExecutionContext(progress=False)
        result = execute_program(program, small_network, context)
        actual_time = result.meta["execution_time"]
        
        # Accuracy within order of magnitude (very conservative test)
        # Real accuracy will vary by hardware
        assert actual_time < estimated_time * 100  # Within 100x
        
        # Check that we track accuracy
        assert "time_accuracy" in result.meta


@pytest.mark.integration
class TestIntegration:
    """Integration tests with real networks."""
    
    def test_full_workflow(self, small_network):
        """Test complete workflow: create, plan, execute."""
        from py3plex.dsl import Q
        
        # Build query
        query_ast = (
            Q.nodes()
            .compute("degree")
            .where(lambda n: n["degree"] > 1)
            .order_by("degree", reverse=True)
            .limit(10)
            .to_ast()
        )
        
        # Create program
        program = GraphProgram.from_ast(query_ast)
        
        # Create context with budget
        context = ExecutionContext.create(
            time_budget="30s",
            n_jobs=2,
            progress=False,
        )
        
        # Execute
        result = execute_program(program, small_network, context)
        
        # Verify results
        assert result is not None
        assert len(result.data) > 0
        assert len(result.data) <= 10
        assert "execution_time" in result.meta
        assert result.meta["execution_time"] < 30.0
    
    def test_optimize_with_budget(self, small_network):
        """Test optimizing program with budget constraint."""
        query_ast = (
            Q.nodes()
            .compute("degree")
            .compute("betweenness_centrality")
            .to_ast()
        )
        
        program = GraphProgram.from_ast(query_ast)
        
        # Optimize with budget
        optimized = program.optimize(budget="10s")
        
        # Both should be valid programs
        assert program.hash() != "" or optimized.hash() != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
