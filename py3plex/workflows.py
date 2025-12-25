"""
Config-driven workflow execution for py3plex.

This module enables users to define and execute complex network analysis
workflows using YAML or JSON configuration files. This is ideal for
reproducible research and automated pipelines.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Union

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import networkx as nx

from py3plex.core import multinet
from py3plex.logging_config import get_logger
from py3plex.exceptions import Py3plexIOError, Py3plexFormatError, AlgorithmError

logger = get_logger(__name__)

# Try to import YAML support
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.debug("PyYAML not available, only JSON configs will be supported")


class WorkflowConfig:
    """Configuration for a network analysis workflow."""

    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize workflow configuration from dictionary.

        Args:
            config_dict: Configuration dictionary with workflow specification
        """
        self.config = config_dict
        self.name = config_dict.get("name", "unnamed_workflow")
        self.description = config_dict.get("description", "")
        self.datasets = config_dict.get("datasets", [])
        self.operations = config_dict.get("operations", [])
        self.output = config_dict.get("output", {})

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "WorkflowConfig":
        """Load workflow configuration from YAML or JSON file.

        Args:
            config_path: Path to configuration file (.yaml, .yml, or .json)

        Returns:
            WorkflowConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            # Try to find similar files in the same directory
            similar_files = []
            if config_path.parent.exists():
                similar_files = [
                    str(f) for f in config_path.parent.glob("*.yaml")
                ] + [
                    str(f) for f in config_path.parent.glob("*.yml")
                ] + [
                    str(f) for f in config_path.parent.glob("*.json")
                ]
            
            raise Py3plexIOError(
                f"Configuration file not found: {config_path}",
                suggestions=[
                    "Check that the file path is correct",
                    "Ensure the file exists and you have read permission"
                ],
                context={"similar_files": similar_files[:5] if similar_files else None}
            )

        # Load based on file extension
        if config_path.suffix in [".yaml", ".yml"]:
            if not HAS_YAML:
                raise Py3plexFormatError(
                    "YAML configuration files require PyYAML",
                    suggestions=[
                        "Install PyYAML: pip install pyyaml",
                        "Alternatively, convert your config to JSON format"
                    ]
                )
            with open(config_path) as f:
                config_dict = yaml.safe_load(f)
        elif config_path.suffix == ".json":
            with open(config_path) as f:
                config_dict = json.load(f)
        else:
            raise Py3plexFormatError(
                f"Unsupported configuration file format: {config_path.suffix}",
                valid_formats=[".yaml", ".yml", ".json"],
                input_format=config_path.suffix
            )

        return cls(config_dict)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not self.datasets:
            errors.append("At least one dataset must be specified")

        if not self.operations:
            errors.append("At least one operation must be specified")

        # Validate datasets
        for i, dataset in enumerate(self.datasets):
            if "name" not in dataset:
                errors.append(f"Dataset {i}: 'name' is required")

            if "type" not in dataset:
                errors.append(f"Dataset {i}: 'type' is required")
            elif dataset["type"] not in ["file", "generate"]:
                errors.append(
                    f"Dataset {i}: type must be 'file' or 'generate', got '{dataset['type']}'"
                )

            if dataset["type"] == "file" and "path" not in dataset:
                errors.append(f"Dataset {i}: 'path' required for type='file'")

            if dataset["type"] == "generate" and "generator" not in dataset:
                errors.append(f"Dataset {i}: 'generator' required for type='generate'")

        # Validate operations
        valid_operations = [
            "stats",
            "community",
            "centrality",
            "visualize",
            "aggregate",
            "convert",
        ]
        for i, operation in enumerate(self.operations):
            if "type" not in operation:
                errors.append(f"Operation {i}: 'type' is required")
            elif operation["type"] not in valid_operations:
                errors.append(
                    f"Operation {i}: invalid type '{operation['type']}'. "
                    f"Valid types: {', '.join(valid_operations)}"
                )

            if "dataset" not in operation:
                errors.append(f"Operation {i}: 'dataset' is required")

        return errors


class WorkflowRunner:
    """Execute network analysis workflows from configuration."""

    def __init__(self, config: WorkflowConfig):
        """Initialize workflow runner.

        Args:
            config: Workflow configuration to execute
        """
        self.config = config
        self.datasets: Dict[str, multinet.multi_layer_network] = {}
        self.results: Dict[str, Any] = {}

    def load_datasets(self) -> None:
        """Load or generate all datasets specified in configuration."""
        logger.info(f"Loading {len(self.config.datasets)} dataset(s)...")

        for dataset_spec in self.config.datasets:
            name = dataset_spec["name"]
            dataset_type = dataset_spec["type"]

            logger.info(f"  Loading dataset '{name}' (type: {dataset_type})...")

            if dataset_type == "file":
                # Load from file
                path = dataset_spec["path"]
                network = self._load_network_from_file(path)
                self.datasets[name] = network

            elif dataset_type == "generate":
                # Generate network
                network = self._generate_network(dataset_spec)
                self.datasets[name] = network

            logger.info(
                f"    Loaded: {network.core_network.number_of_nodes()} nodes, "
                f"{network.core_network.number_of_edges()} edges"
            )

    def _load_network_from_file(self, path: str) -> multinet.multi_layer_network:
        """Load network from file.

        Args:
            path: Path to network file

        Returns:
            Loaded multi_layer_network
        """
        network = multinet.multi_layer_network()
        file_path = Path(path)

        if file_path.suffix in [".graphml"]:
            G = nx.read_graphml(str(path))
            network.core_network = G
            network.directed = G.is_directed()
        elif file_path.suffix == ".gpickle":
            network.load_network(path, input_type="gpickle")
        else:
            # Try multiedgelist format
            network.load_network(path, input_type="multiedgelist")

        return network

    def _generate_network(self, spec: Dict[str, Any]) -> multinet.multi_layer_network:
        """Generate network from specification.

        Args:
            spec: Generator specification

        Returns:
            Generated multi_layer_network
        """
        generator = spec["generator"]
        params = spec.get("parameters", {})

        network = multinet.multi_layer_network()

        if generator == "random":
            # Generate random multilayer network
            nodes = params.get("nodes", 10)
            layers = params.get("layers", 2)
            probability = params.get("probability", 0.1)
            seed = params.get("seed")

            # Use local Random instance to avoid global state changes
            rng = random.Random(seed) if seed is not None else random.Random()

            # Create layers with nodes and edges
            for layer_idx in range(layers):
                layer_name = f"layer{layer_idx + 1}"

                # Add nodes
                nodes_dict = [
                    {"source": f"node{i}", "type": layer_name} for i in range(nodes)
                ]
                network.add_nodes(nodes_dict, input_type="dict")

                # Add edges
                edges_dict = []
                for i in range(nodes):
                    for j in range(i + 1, nodes):
                        if rng.random() < probability:
                            edges_dict.append(
                                {
                                    "source": f"node{i}",
                                    "target": f"node{j}",
                                    "source_type": layer_name,
                                    "target_type": layer_name,
                                }
                            )
                if edges_dict:
                    network.add_edges(edges_dict, input_type="dict")

        else:
            valid_generators = ["random"]
            raise Py3plexFormatError(
                f"Unknown network generator: '{generator}'",
                valid_formats=valid_generators,
                input_format=generator,
                suggestions=[
                    "Use 'random' generator for Erdős-Rényi multilayer networks",
                    "Check the documentation for available generators"
                ]
            )

        return network

    def execute_operations(self) -> None:
        """Execute all operations specified in configuration."""
        logger.info(f"Executing {len(self.config.operations)} operation(s)...")

        for i, operation in enumerate(self.config.operations):
            op_type = operation["type"]
            dataset_name = operation["dataset"]
            params = operation.get("parameters", {})

            logger.info(f"  Operation {i+1}: {op_type} on dataset '{dataset_name}'...")

            if dataset_name not in self.datasets:
                logger.error(f"    Dataset '{dataset_name}' not found, skipping")
                continue

            network = self.datasets[dataset_name]

            try:
                result = self._execute_operation(op_type, network, params)
                result_key = f"{dataset_name}_{op_type}_{i}"
                self.results[result_key] = result
                logger.info(f"    Completed: {result_key}")
            except Exception as e:
                logger.error(f"    Failed: {e}")

    def _execute_operation(
        self,
        op_type: str,
        network: multinet.multi_layer_network,
        params: Dict[str, Any],
    ) -> Any:
        """Execute a single operation.

        Args:
            op_type: Type of operation
            network: Network to operate on
            params: Operation parameters

        Returns:
            Operation result
        """
        if op_type == "stats":
            return self._compute_stats(network, params)
        elif op_type == "community":
            return self._detect_communities(network, params)
        elif op_type == "centrality":
            return self._compute_centrality(network, params)
        elif op_type == "visualize":
            return self._visualize(network, params)
        elif op_type == "aggregate":
            return self._aggregate(network, params)
        elif op_type == "convert":
            return self._convert(network, params)
        else:
            valid_operations = ["stats", "community", "centrality", "visualize", "aggregate", "convert"]
            from py3plex.errors import find_similar
            did_you_mean = find_similar(op_type, valid_operations)
            raise Py3plexFormatError(
                f"Unknown workflow operation type: '{op_type}'",
                valid_formats=valid_operations,
                input_format=op_type,
                suggestions=[f"Valid operations: {', '.join(valid_operations)}"],
                did_you_mean=did_you_mean
            )

    def _compute_stats(
        self, network: multinet.multi_layer_network, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute network statistics."""
        from py3plex.algorithms.statistics import multilayer_statistics as mls

        stats = {}
        stats["nodes"] = network.core_network.number_of_nodes()
        stats["edges"] = network.core_network.number_of_edges()

        # Layer densities
        layers = self._get_layer_names(network)
        if layers:
            stats["layer_densities"] = {
                layer: float(mls.layer_density(network, layer)) for layer in layers
            }

        return stats

    def _detect_communities(
        self, network: multinet.multi_layer_network, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect communities in network."""
        from py3plex.algorithms.community_detection import community_wrapper

        algorithm = params.get("algorithm", "louvain")

        G = (
            network.core_network.to_undirected()
            if network.core_network.is_directed()
            else network.core_network
        )

        if algorithm == "louvain":
            partition = community_wrapper.louvain_communities(G)
            communities = {str(node): int(comm) for node, comm in partition.items()}
        else:
            valid_algorithms = ["louvain"]
            raise AlgorithmError(
                f"Community detection algorithm '{algorithm}' is not available",
                algorithm_name=algorithm,
                valid_algorithms=valid_algorithms,
                suggestions=[
                    "Use 'louvain' for fast modularity-based community detection",
                    "Check available algorithms in py3plex.algorithms.community_detection"
                ]
            )

        num_communities = len(set(communities.values()))

        return {
            "algorithm": algorithm,
            "num_communities": num_communities,
            "communities": communities,
        }

    def _compute_centrality(
        self, network: multinet.multi_layer_network, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute centrality measures."""
        measure = params.get("measure", "degree")

        G = (
            network.core_network.to_undirected()
            if network.directed
            else network.core_network
        )

        if measure == "degree":
            centrality = dict(G.degree())
        elif measure == "betweenness":
            centrality = nx.betweenness_centrality(G)
        elif measure == "closeness":
            centrality = nx.closeness_centrality(G)
        else:
            valid_measures = ["degree", "betweenness", "closeness"]
            from py3plex.errors import find_similar
            did_you_mean = find_similar(measure, valid_measures)
            raise AlgorithmError(
                f"Centrality measure '{measure}' is not available",
                algorithm_name=measure,
                valid_algorithms=valid_measures,
                suggestions=[
                    f"Valid measures: {', '.join(valid_measures)}",
                    "Use 'degree' for local connectivity",
                    "Use 'betweenness' for bridge nodes",
                    "Use 'closeness' for nodes close to all others"
                ],
                did_you_mean=did_you_mean
            )

        centrality_data = {
            str(node): float(score) for node, score in centrality.items()
        }

        return {"measure": measure, "centrality": centrality_data}

    def _visualize(
        self, network: multinet.multi_layer_network, params: Dict[str, Any]
    ) -> str:
        """Visualize network."""
        output = params.get("output", "network.png")
        layout = params.get("layout", "spring")

        if layout == "spring":
            pos = nx.spring_layout(network.core_network)
        elif layout == "circular":
            pos = nx.circular_layout(network.core_network)
        else:
            pos = nx.spring_layout(network.core_network)

        plt.figure(figsize=(10, 8))
        nx.draw(
            network.core_network,
            pos,
            node_size=100,
            node_color="lightblue",
            edge_color="gray",
            alpha=0.7,
            with_labels=False,
        )
        plt.savefig(output, dpi=150, bbox_inches="tight")
        plt.close()

        return output

    def _aggregate(
        self, network: multinet.multi_layer_network, params: Dict[str, Any]
    ) -> multinet.multi_layer_network:
        """Aggregate multilayer network."""
        method = params.get("method", "sum")
        aggregated = network.aggregate_edges(metric=method)
        return aggregated

    def _convert(
        self, network: multinet.multi_layer_network, params: Dict[str, Any]
    ) -> str:
        """Convert network format."""
        output = params.get("output", "network.graphml")
        output_path = Path(output)

        if output_path.suffix == ".graphml":
            nx.write_graphml(network.core_network, str(output_path))
        elif output_path.suffix == ".json":
            data = {
                "nodes": [str(n) for n in network.core_network.nodes()],
                "edges": [
                    {"source": str(u), "target": str(v)}
                    for u, v in network.core_network.edges()
                ],
            }
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            valid_formats = [".graphml", ".gexf", ".gml", ".edgelist", ".json"]
            raise Py3plexFormatError(
                f"Unsupported output format: {output_path.suffix}",
                valid_formats=valid_formats,
                input_format=output_path.suffix,
                suggestions=[
                    "Use .graphml for rich network data with attributes",
                    "Use .json for simple edge lists",
                    "Use .edgelist for plain text format"
                ]
            )

        return str(output_path)

    def _get_layer_names(self, network: multinet.multi_layer_network) -> List[str]:
        """Extract layer names from network."""
        layers = set()
        try:
            for node in network.core_network.nodes():
                if isinstance(node, tuple) and len(node) >= 2:
                    layers.add(node[1])
        except Exception:
            pass
        return sorted(layers)

    def save_results(self) -> None:
        """Save workflow results to output files."""
        output_config = self.config.output

        if not output_config:
            logger.info("No output configuration specified, skipping save")
            return

        output_dir = output_config.get("directory", ".")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save summary
        summary_file = output_path / output_config.get("summary", "summary.json")
        with open(summary_file, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {summary_file}")

    def run(self) -> None:
        """Execute the complete workflow."""
        logger.info(f"Starting workflow: {self.config.name}")

        if self.config.description:
            logger.info(f"Description: {self.config.description}")

        # Validate configuration
        errors = self.config.validate()
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise Py3plexFormatError(
                "Workflow configuration validation failed",
                suggestions=[
                    "Check the configuration file for missing required fields",
                    "Ensure all dataset and operation specifications are complete",
                    f"Found {len(errors)} validation error(s) - see log for details"
                ],
                notes=errors[:3]  # Include first 3 errors as notes
            )

        # Execute workflow steps
        try:
            self.load_datasets()
            self.execute_operations()
            self.save_results()
            logger.info("Workflow completed successfully")
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise


def run_workflow(config_path: Union[str, Path]) -> None:
    """Run a workflow from configuration file.

    Args:
        config_path: Path to YAML or JSON configuration file

    Example:
        >>> from py3plex.workflows import run_workflow
        >>> run_workflow("my_experiment.yaml")
    """
    config = WorkflowConfig.from_file(config_path)
    runner = WorkflowRunner(config)
    runner.run()
