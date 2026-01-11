"""In-memory network handle registry for MCP server.

Manages loaded networks with unique identifiers.
"""

import time
import uuid
from typing import Any, Dict, Optional

from py3plex_mcp.errors import NetworkNotFoundError


class NetworkRegistry:
    """Registry for storing loaded networks."""

    def __init__(self):
        """Initialize empty registry."""
        self._networks: Dict[str, Dict[str, Any]] = {}

    def add(
        self,
        network: Any,
        source: str,
        net_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add network to registry.

        Args:
            network: multi_layer_network instance
            source: Source path or description
            net_id: Optional custom network ID. If None, generates UUID.
            metadata: Optional additional metadata

        Returns:
            Network ID (handle)
        """
        if net_id is None:
            net_id = str(uuid.uuid4())[:8]

        # Ensure unique
        if net_id in self._networks:
            counter = 1
            while f"{net_id}_{counter}" in self._networks:
                counter += 1
            net_id = f"{net_id}_{counter}"

        self._networks[net_id] = {
            "network": network,
            "source": source,
            "created_at": time.time(),
            "metadata": metadata or {},
        }

        return net_id

    def get(self, net_id: str) -> Any:
        """Get network by ID.

        Args:
            net_id: Network ID

        Returns:
            multi_layer_network instance

        Raises:
            NetworkNotFoundError: If network not found
        """
        if net_id not in self._networks:
            raise NetworkNotFoundError(net_id)

        return self._networks[net_id]["network"]

    def get_info(self, net_id: str) -> Dict[str, Any]:
        """Get network metadata.

        Args:
            net_id: Network ID

        Returns:
            Dict with source, created_at, metadata

        Raises:
            NetworkNotFoundError: If network not found
        """
        if net_id not in self._networks:
            raise NetworkNotFoundError(net_id)

        entry = self._networks[net_id]
        return {
            "net_id": net_id,
            "source": entry["source"],
            "created_at": entry["created_at"],
            "metadata": entry["metadata"],
        }

    def remove(self, net_id: str) -> None:
        """Remove network from registry.

        Args:
            net_id: Network ID

        Raises:
            NetworkNotFoundError: If network not found
        """
        if net_id not in self._networks:
            raise NetworkNotFoundError(net_id)

        del self._networks[net_id]

    def list_all(self) -> list:
        """List all network handles.

        Returns:
            List of dicts with net_id, source, created_at
        """
        result = []
        for net_id, entry in self._networks.items():
            result.append(
                {
                    "net_id": net_id,
                    "source": entry["source"],
                    "created_at": entry["created_at"],
                }
            )
        return result

    def clear(self) -> None:
        """Clear all networks from registry."""
        self._networks.clear()


# Global registry instance
_registry = NetworkRegistry()


def get_registry() -> NetworkRegistry:
    """Get global registry instance."""
    return _registry
