"""
I/O Service - File loading and saving with progress tracking.

Handles various graph file formats and provides non-blocking APIs
for loading/saving networks with progress callbacks.
"""

import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import networkx as nx

from .logger import get_logger

logger = get_logger()


class IOService:
    """Service for loading and saving graph files."""

    # Supported file formats
    FORMATS = {
        ".edgelist": "edgelist",
        ".gml": "gml",
        ".graphml": "graphml",
        ".gpickle": "pickle",
        ".pkl": "pickle",
        ".pickle": "pickle",
        ".json": "json",
        ".txt": "edgelist",
    }

    def __init__(self):
        """Initialize I/O service."""
        self.current_graph: Optional[nx.Graph] = None
        self.current_file: Optional[str] = None
        self.graph_metadata: Dict[str, Any] = {}

    def detect_format(self, filepath: str) -> Optional[str]:
        """Detect file format from extension."""
        ext = Path(filepath).suffix.lower()
        return self.FORMATS.get(ext)

    def load_graph(
        self,
        filepath: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[nx.Graph]:
        """
        Load a graph from file.
        
        Args:
            filepath: Path to graph file
            progress_callback: Optional callback(percent, message)
            
        Returns:
            NetworkX graph or None on error
        """
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            if progress_callback:
                progress_callback(0, "Detecting format...")

            file_format = self.detect_format(filepath)
            if not file_format:
                raise ValueError(f"Unsupported file format: {filepath}")

            logger.info(f"Loading {file_format} file: {filepath}")

            if progress_callback:
                progress_callback(20, f"Loading {file_format} file...")

            # Load based on format
            if file_format == "edgelist":
                graph = nx.read_edgelist(filepath)
            elif file_format == "gml":
                graph = nx.read_gml(filepath)
            elif file_format == "graphml":
                graph = nx.read_graphml(filepath)
            elif file_format == "pickle":
                graph = nx.read_gpickle(filepath)
            elif file_format == "json":
                from networkx.readwrite import json_graph
                import json
                with open(filepath, 'r') as f:
                    data = json.load(f)
                graph = json_graph.node_link_graph(data)
            else:
                raise ValueError(f"Format {file_format} not yet implemented")

            if progress_callback:
                progress_callback(80, "Computing metadata...")

            # Compute metadata
            self.graph_metadata = self._compute_metadata(graph)

            if progress_callback:
                progress_callback(100, "Complete")

            # Store current graph
            self.current_graph = graph
            self.current_file = filepath

            logger.info(f"Loaded graph with {graph.number_of_nodes()} nodes, "
                       f"{graph.number_of_edges()} edges")

            return graph

        except Exception as e:
            logger.error(f"Error loading graph: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return None

    def save_graph(
        self,
        graph: nx.Graph,
        filepath: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """
        Save a graph to file.
        
        Args:
            graph: NetworkX graph to save
            filepath: Output file path
            progress_callback: Optional callback(percent, message)
            
        Returns:
            True on success, False on error
        """
        try:
            if progress_callback:
                progress_callback(0, "Detecting format...")

            file_format = self.detect_format(filepath)
            if not file_format:
                raise ValueError(f"Unsupported file format: {filepath}")

            logger.info(f"Saving {file_format} file: {filepath}")

            if progress_callback:
                progress_callback(20, f"Saving {file_format} file...")

            # Ensure parent directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # Save based on format
            if file_format == "edgelist":
                nx.write_edgelist(graph, filepath)
            elif file_format == "gml":
                nx.write_gml(graph, filepath)
            elif file_format == "graphml":
                nx.write_graphml(graph, filepath)
            elif file_format == "pickle":
                nx.write_gpickle(graph, filepath)
            elif file_format == "json":
                from networkx.readwrite import json_graph
                import json
                data = json_graph.node_link_data(graph)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Format {file_format} not yet implemented")

            if progress_callback:
                progress_callback(100, "Complete")

            logger.info(f"Saved graph to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving graph: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False

    def _compute_metadata(self, graph: nx.Graph) -> Dict[str, Any]:
        """Compute graph metadata."""
        metadata = {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "directed": graph.is_directed(),
            "multigraph": graph.is_multigraph(),
        }

        # Try to compute additional metrics (may be expensive for large graphs)
        try:
            if graph.number_of_nodes() < 10000:  # Only for smaller graphs
                metadata["density"] = nx.density(graph)
                if nx.is_connected(graph):
                    metadata["diameter"] = nx.diameter(graph)
                metadata["components"] = nx.number_connected_components(graph)
        except Exception as e:
            logger.debug(f"Could not compute all metrics: {e}")

        return metadata

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata for currently loaded graph."""
        return self.graph_metadata.copy()

    def get_current_graph(self) -> Optional[nx.Graph]:
        """Get the currently loaded graph."""
        return self.current_graph

    def get_current_file(self) -> Optional[str]:
        """Get the currently loaded file path."""
        return self.current_file

    def clear(self) -> None:
        """Clear current graph and metadata."""
        self.current_graph = None
        self.current_file = None
        self.graph_metadata = {}
        logger.info("Cleared current graph")

    @staticmethod
    def validate_file(filepath: str) -> tuple[bool, str]:
        """
        Validate if a file can be loaded.
        
        Returns:
            (is_valid, error_message)
        """
        if not os.path.exists(filepath):
            return False, "File does not exist"

        if not os.path.isfile(filepath):
            return False, "Path is not a file"

        if os.path.getsize(filepath) == 0:
            return False, "File is empty"

        ext = Path(filepath).suffix.lower()
        if ext not in IOService.FORMATS:
            return False, f"Unsupported format: {ext}"

        return True, ""


# Singleton instance
_io_service: Optional[IOService] = None


def get_io_service() -> IOService:
    """Get the global I/O service instance."""
    global _io_service
    if _io_service is None:
        _io_service = IOService()
    return _io_service
