import { useState, useEffect, useRef, useMemo, useCallback, MouseEvent } from 'react';
import { Play, AlertCircle } from 'lucide-react';
import { getGraphPositions } from '../lib/api';

interface NodePosition {
  node_id: string;
  x: number;
  y: number;
  z?: number;
  layer?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  layer?: string;
}

interface GraphPositionsResponse {
  graph_id: string;
  positions: NodePosition[];
  edges: GraphEdge[];
}

const LAYER_COLORS = [
  '#2563eb', // blue-600
  '#dc2626', // red-600
  '#16a34a', // green-600
  '#d97706', // amber-600
  '#7c3aed', // violet-600
  '#0891b2', // cyan-600
  '#db2777', // pink-600
  '#65a30d', // lime-600
];

function layerColor(layer: string, allLayers: string[]) {
  const idx = allLayers.indexOf(layer);
  return LAYER_COLORS[idx >= 0 ? idx % LAYER_COLORS.length : 0];
}

const HIT_TEST_RADIUS_PX = 10;
const CANVAS_PADDING_PX = 24;

export default function Visualize() {
  const [graphId, setGraphId] = useState<string | null>(null);
  const [positions, setPositions] = useState<GraphPositionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const storedGraphId = sessionStorage.getItem('currentGraphId') || localStorage.getItem('currentGraphId');
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
      const data: GraphPositionsResponse = response.data;
      setPositions(data);
      setVisibleLayers(new Set((data.edges || []).map((e) => e.layer || 'default')));
      setSelectedNode(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load positions');
    } finally {
      setLoading(false);
    }
  };

  // Layers come from edge data, not node data -- this backend tags layer
  // membership on edges (a node can touch several layers via different
  // edges), so there is no single well-defined "layer" per node to color
  // nodes by.
  const layers = useMemo(() => {
    if (!positions) return [];
    return Array.from(new Set((positions.edges || []).map((e) => e.layer || 'default'))).sort();
  }, [positions]);

  const degreeById = useMemo(() => {
    const map = new Map<string, number>();
    if (!positions) return map;
    for (const e of positions.edges || []) {
      map.set(e.source, (map.get(e.source) || 0) + 1);
      map.set(e.target, (map.get(e.target) || 0) + 1);
    }
    return map;
  }, [positions]);

  // Bounding box of the raw layout coordinates, used to fit everything
  // into the canvas regardless of the coordinate scale the backend used.
  const bounds = useMemo(() => {
    if (!positions || positions.positions.length === 0) return null;
    const xs = positions.positions.map((p) => p.x);
    const ys = positions.positions.map((p) => p.y);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const width = Math.max(...xs) - minX || 1;
    const height = Math.max(...ys) - minY || 1;
    return { minX, minY, width, height };
  }, [positions]);

  const toScreen = useCallback(
    (x: number, y: number, rectWidth: number, rectHeight: number) => {
      if (!bounds) return [0, 0];
      const scale = Math.min(
        (rectWidth - 2 * CANVAS_PADDING_PX) / bounds.width,
        (rectHeight - 2 * CANVAS_PADDING_PX) / bounds.height
      );
      return [
        CANVAS_PADDING_PX + (x - bounds.minX) * scale,
        CANVAS_PADDING_PX + (y - bounds.minY) * scale,
      ];
    },
    [bounds]
  );

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !positions || !bounds) return;

    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);

    const nodeById = new Map(positions.positions.map((p) => [p.node_id, p]));

    ctx.lineWidth = 1;
    for (const e of positions.edges || []) {
      const layer = e.layer || 'default';
      if (!visibleLayers.has(layer)) continue;
      const s = nodeById.get(e.source);
      const t = nodeById.get(e.target);
      if (!s || !t) continue;
      const [sx, sy] = toScreen(s.x, s.y, rect.width, rect.height);
      const [tx, ty] = toScreen(t.x, t.y, rect.width, rect.height);
      ctx.strokeStyle = layerColor(layer, layers);
      ctx.globalAlpha = 0.45;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(tx, ty);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    for (const p of positions.positions) {
      const [sx, sy] = toScreen(p.x, p.y, rect.width, rect.height);
      const isSelected = p.node_id === selectedNode;
      ctx.beginPath();
      ctx.arc(sx, sy, isSelected ? 6 : 4, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? '#111827' : '#475569';
      ctx.fill();
      if (isSelected) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#2563eb';
        ctx.stroke();
      }
    }
  }, [positions, bounds, visibleLayers, layers, selectedNode, toScreen]);

  useEffect(() => {
    draw();
  }, [draw]);

  useEffect(() => {
    window.addEventListener('resize', draw);
    return () => window.removeEventListener('resize', draw);
  }, [draw]);

  const handleCanvasClick = (event: MouseEvent<HTMLCanvasElement>) => {
    if (!positions || !bounds) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    let closest: string | null = null;
    let closestDist = HIT_TEST_RADIUS_PX;
    for (const p of positions.positions) {
      const [sx, sy] = toScreen(p.x, p.y, rect.width, rect.height);
      const dist = Math.hypot(sx - clickX, sy - clickY);
      if (dist < closestDist) {
        closestDist = dist;
        closest = p.node_id;
      }
    }
    setSelectedNode(closest);
  };

  const toggleLayer = (layer: string) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layer)) {
        next.delete(layer);
      } else {
        next.add(layer);
      }
      return next;
    });
  };

  if (!graphId) {
    return (
      <div className="px-4 py-6">
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
          <AlertCircle className="h-6 w-6 text-yellow-600 dark:text-yellow-400 mb-2" />
          <h3 className="text-lg font-medium text-yellow-900 dark:text-yellow-100">No Graph Loaded</h3>
          <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
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

  const selectedPosition = positions?.positions.find((p) => p.node_id === selectedNode) || null;

  return (
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Visualize Network</h1>

      <div className="grid grid-cols-4 gap-6">
        {/* Layer Panel */}
        <div className="col-span-1 bg-white dark:bg-gray-800 shadow rounded-lg p-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">Layers</h2>
          {layers.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No layer information available</p>
          ) : (
            <ul className="space-y-2">
              {layers.map((layer) => (
                <li key={layer} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={visibleLayers.has(layer)}
                    onChange={() => toggleLayer(layer)}
                  />
                  <span
                    className="inline-block w-3 h-3 rounded-full"
                    style={{ backgroundColor: layerColor(layer, layers) }}
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{layer}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Graph Canvas */}
        <div className="col-span-2 bg-white dark:bg-gray-800 shadow rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Network View</h2>
            <button className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              <Play className="h-4 w-4 inline mr-1" />
              Recompute Layout
            </button>
          </div>

          {loading && (
            <div className="flex items-center justify-center h-96 bg-gray-50 dark:bg-gray-700 rounded">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400">Loading visualization...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded p-4">
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}

          {positions && !loading && !error && (
            <div className="h-96 bg-gray-50 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600 overflow-hidden">
              <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                className="w-full h-full cursor-pointer"
              />
            </div>
          )}

          {positions && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              {positions.positions.length} nodes, {positions.edges?.length || 0} edges
              {selectedNode ? ' -- click another node or empty space to change selection' : ' -- click a node for details'}
            </p>
          )}
        </div>

        {/* Inspect Panel */}
        <div className="col-span-1 bg-white dark:bg-gray-800 shadow rounded-lg p-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">Inspect</h2>
          {selectedPosition ? (
            <dl className="text-sm space-y-2">
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Node ID</dt>
                <dd className="text-gray-900 dark:text-gray-100 font-mono break-all">{selectedPosition.node_id}</dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Degree</dt>
                <dd className="text-gray-900 dark:text-gray-100">{degreeById.get(selectedPosition.node_id) || 0}</dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Position</dt>
                <dd className="text-gray-900 dark:text-gray-100">
                  ({selectedPosition.x.toFixed(2)}, {selectedPosition.y.toFixed(2)})
                </dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Select a node or edge to view details
            </p>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="mt-6 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Note:</strong> This is a minimal Canvas 2D renderer (plain nodes/lines,
          no pan/zoom/drag). Edges are colored and toggled by layer; layer is an edge
          attribute in this data model, not a node attribute, so nodes are not
          colored by layer. "Recompute Layout" is not wired up yet -- it requires the
          async layout job pipeline (Celery worker), which is separate from rendering.
        </p>
      </div>
    </div>
  );
}