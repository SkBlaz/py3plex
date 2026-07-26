import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { AlertCircle } from 'lucide-react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import { getGraphPositions } from '../lib/api';
import SigmaRenderer from '../components/SigmaRenderer';

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

// The backend's spring-layout coordinates are typically in [-1, 1];
// Cytoscape's preset layout uses them as raw pixel positions, so scale up
// to something legible on screen. Sigma auto-fits the camera to whatever
// coordinate range it's given, so it doesn't need this scaling.
const LAYOUT_SCALE = 300;

// Matches the backend's own spring-layout vs. random-layout cutoff
// (gui/api/app/services/model.py) -- past this node count Cytoscape's
// SVG/canvas hybrid rendering gets sluggish, so default to the WebGL-based
// Sigma.js renderer instead.
const SIGMA_AUTO_THRESHOLD = 1000;

type RendererChoice = 'auto' | 'cytoscape' | 'sigma';

export default function Visualize() {
  const [graphId, setGraphId] = useState<string | null>(null);
  const [positions, setPositions] = useState<GraphPositionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [rendererChoice, setRendererChoice] = useState<RendererChoice>('auto');

  const cyRef = useRef<cytoscape.Core | null>(null);

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

  const filteredEdges = useMemo((): GraphEdge[] => {
    if (!positions) return [];
    return (positions.edges || []).filter((e) => visibleLayers.has(e.layer || 'default'));
  }, [positions, visibleLayers]);

  // Below the threshold, Cytoscape's richer interactions (drag-to-reposition,
  // curved edges) are worth it; above it, Sigma's WebGL rendering is worth
  // the tradeoff to stay responsive. Mirrors SIGMA_AUTO_THRESHOLD.
  const effectiveRenderer = useMemo((): 'cytoscape' | 'sigma' => {
    if (rendererChoice !== 'auto') return rendererChoice;
    return (positions?.positions.length || 0) > SIGMA_AUTO_THRESHOLD ? 'sigma' : 'cytoscape';
  }, [rendererChoice, positions]);

  const elements = useMemo((): cytoscape.ElementDefinition[] => {
    if (!positions) return [];
    const nodeEls: cytoscape.ElementDefinition[] = positions.positions.map((p) => ({
      data: { id: p.node_id },
      position: { x: p.x * LAYOUT_SCALE, y: p.y * LAYOUT_SCALE },
    }));
    const edgeEls: cytoscape.ElementDefinition[] = filteredEdges.map((e, i) => ({
      data: {
        id: `e${i}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        layer: e.layer || 'default',
      },
    }));
    return [...nodeEls, ...edgeEls];
  }, [positions, filteredEdges]);

  const stylesheet = useMemo((): cytoscape.StylesheetStyle[] => {
    const base: cytoscape.StylesheetStyle[] = [
      {
        selector: 'node',
        style: {
          'background-color': '#475569',
          width: 10,
          height: 10,
        },
      },
      {
        selector: 'node:selected',
        style: {
          'background-color': '#111827',
          'border-width': 2,
          'border-color': '#2563eb',
        },
      },
      {
        // 'bezier' (unlike 'haystack') automatically fans out parallel
        // edges -- e.g. the same two nodes connected in multiple layers --
        // instead of drawing them exactly on top of each other.
        selector: 'edge',
        style: {
          width: 1.5,
          'curve-style': 'bezier',
          opacity: 0.55,
        },
      },
    ];
    const layerStyles: cytoscape.StylesheetStyle[] = layers.map((layer) => ({
      selector: `edge[layer = "${layer}"]`,
      style: { 'line-color': layerColor(layer, layers) },
    }));
    return [...base, ...layerStyles];
  }, [layers]);

  const handleCyInit = useCallback((cy: cytoscape.Core) => {
    cyRef.current = cy;
    cy.on('tap', 'node', (evt) => {
      setSelectedNode(evt.target.id());
    });
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });
  }, []);

  // Keep Cytoscape's own selection state in sync with React state (e.g.
  // cleared on reload, or if selection is ever driven from elsewhere).
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().unselect();
    if (selectedNode) {
      cy.getElementById(selectedNode).select();
    }
  }, [selectedNode, elements]);

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
            <ul className="space-y-2 max-h-96 overflow-y-auto pr-1 scrollbar-visible">
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
            <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
              Renderer
              <select
                className="border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-xs px-2 py-1"
                value={rendererChoice}
                onChange={(e) => setRendererChoice(e.target.value as RendererChoice)}
              >
                <option value="auto">Auto ({effectiveRenderer === 'sigma' ? 'Sigma.js' : 'Cytoscape.js'})</option>
                <option value="cytoscape">Cytoscape.js</option>
                <option value="sigma">Sigma.js (WebGL)</option>
              </select>
            </label>
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
              {effectiveRenderer === 'sigma' ? (
                <SigmaRenderer
                  nodes={positions.positions}
                  edges={filteredEdges}
                  layerColor={layerColor}
                  layers={layers}
                  selectedNode={selectedNode}
                  onSelectNode={setSelectedNode}
                />
              ) : (
                <CytoscapeComponent
                  elements={elements}
                  stylesheet={stylesheet}
                  layout={{ name: 'preset' }}
                  style={{ width: '100%', height: '100%' }}
                  cy={handleCyInit}
                />
              )}
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
          <strong>Note:</strong> Rendered with{' '}
          {effectiveRenderer === 'sigma' ? 'Sigma.js (WebGL)' : 'Cytoscape.js'} - drag
          empty space to pan, scroll to zoom
          {effectiveRenderer === 'cytoscape' ? ', drag a node to reposition it' : ''}.
          Edges are colored and toggled by layer; layer is an edge attribute in this
          data model, not a node attribute, so nodes are not colored by layer.
          Graphs over {SIGMA_AUTO_THRESHOLD} nodes switch to Sigma.js automatically
          for performance; use the Renderer dropdown above to override. Layout
          recomputation is not wired up here - it requires the async layout job
          pipeline (Celery worker), which is separate from rendering.
        </p>
      </div>
    </div>
  );
}