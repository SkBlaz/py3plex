import { useState, useEffect } from 'react';
import { Play, AlertCircle } from 'lucide-react';
import { getGraphPositions } from '../lib/api';

export default function Visualize() {
  const [graphId, setGraphId] = useState<string | null>(null);
  const [positions, setPositions] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedGraphId = sessionStorage.getItem('currentGraphId');
    if (storedGraphId) {
      setGraphId(storedGraphId);
      loadPositions(storedGraphId);
    }
  }, []);

  const loadPositions = async (gid: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getGraphPositions(gid);
      setPositions(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load positions');
    } finally {
      setLoading(false);
    }
  };

  if (!graphId) {
    return (
      <div className="px-4 py-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <AlertCircle className="h-6 w-6 text-yellow-600 mb-2" />
          <h3 className="text-lg font-medium text-yellow-900">No Graph Loaded</h3>
          <p className="text-sm text-yellow-800 mt-1">
            Please upload a network file first in the Load Data page.
          </p>
          <a
            href="/"
            className="mt-4 inline-block px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
          >
            Go to Load Data
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Visualize Network</h1>

      <div className="grid grid-cols-4 gap-6">
        {/* Layer Panel */}
        <div className="col-span-1 bg-white shadow rounded-lg p-4">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Layers</h2>
          <p className="text-sm text-gray-500">Layer controls will appear here</p>
        </div>

        {/* Graph Canvas */}
        <div className="col-span-2 bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900">Network View</h2>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              <Play className="h-4 w-4 inline mr-1" />
              Recompute Layout
            </button>
          </div>

          {loading && (
            <div className="flex items-center justify-center h-96 bg-gray-50 rounded">
              <p className="text-gray-500">Loading visualization...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {positions && !loading && (
            <div className="h-96 bg-gray-50 rounded border border-gray-200 flex items-center justify-center">
              <div className="text-center">
                <p className="text-gray-600 mb-2">
                  Graph with {positions.positions?.length || 0} nodes
                </p>
                <p className="text-sm text-gray-500">
                  Canvas visualization would render here
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  (In production: WebGL/Canvas 2D rendering)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Inspect Panel */}
        <div className="col-span-1 bg-white shadow rounded-lg p-4">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Inspect</h2>
          <p className="text-sm text-gray-500">
            Select a node or edge to view details
          </p>
        </div>
      </div>

      {/* Info */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> This is a functional prototype. Full canvas rendering 
          with layer toggles, node selection, and interactive controls would be 
          implemented in production using libraries like D3.js, Cytoscape.js, or WebGL.
        </p>
      </div>
    </div>
  );
}
