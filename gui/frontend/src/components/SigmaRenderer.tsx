import { useEffect, useRef } from 'react';
import { MultiGraph } from 'graphology';
import Sigma from 'sigma';
import { EdgeLineProgram } from 'sigma/rendering';
import EdgeCurveProgram, { DEFAULT_EDGE_CURVATURE, indexParallelEdgesIndex } from '@sigma/edge-curve';

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

interface SigmaRendererProps {
  nodes: NodePosition[];
  edges: GraphEdge[];
  layerColor: (layer: string, allLayers: string[]) => string;
  layers: string[];
  selectedNode: string | null;
  onSelectNode: (nodeId: string | null) => void;
}

const NODE_COLOR = '#475569';
const SELECTED_NODE_COLOR = '#111827';
const NODE_SIZE = 3;
const SELECTED_NODE_SIZE = 6;

// Spreads parallel edges (same node pair, e.g. connected in several layers)
// into increasingly curved arcs instead of overlapping straight lines;
// mirrors sigma.js's own recommended pattern for @sigma/edge-curve.
function curvatureForIndex(index: number, maxIndex: number): number {
  if (maxIndex <= 0) return 0;
  const amplitude = 3.5;
  const maxCurvature = amplitude * (1 - Math.exp(-maxIndex / amplitude)) * DEFAULT_EDGE_CURVATURE;
  return (maxCurvature * index) / maxIndex;
}

// WebGL-backed renderer for graphs too large for Cytoscape's SVG/canvas
// hybrid rendering to stay responsive on (tens of) thousands of nodes.
export default function SigmaRenderer({
  nodes,
  edges,
  layerColor,
  layers,
  selectedNode,
  onSelectNode,
}: SigmaRendererProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const graphRef = useRef<MultiGraph | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // A MultiGraph (not a plain Graph) is required here -- the backend can
    // send several edges between the same two nodes (one per layer), and a
    // plain Graph silently drops every edge after the first between a pair.
    const graph = new MultiGraph();
    for (const n of nodes) {
      graph.addNode(n.node_id, {
        x: n.x,
        y: n.y,
        size: NODE_SIZE,
        color: NODE_COLOR,
        label: n.node_id,
      });
    }
    for (const e of edges) {
      if (!graph.hasNode(e.source) || !graph.hasNode(e.target)) continue;
      const layer = e.layer || 'default';
      graph.addEdge(e.source, e.target, {
        color: layerColor(layer, layers),
        size: 0.5,
      });
    }

    // Identify parallel edges and curve them so they fan out visibly
    // instead of rendering on top of each other; edges with no parallel
    // counterpart stay straight (cheaper to render).
    indexParallelEdgesIndex(graph);
    graph.forEachEdge(
      (edge, { parallelIndex, parallelMinIndex, parallelMaxIndex }) => {
        if (typeof parallelMinIndex === 'number') {
          graph.mergeEdgeAttributes(edge, {
            type: parallelIndex ? 'curved' : 'straight',
            curvature: curvatureForIndex(parallelIndex, parallelMaxIndex),
          });
        } else if (typeof parallelIndex === 'number') {
          graph.mergeEdgeAttributes(edge, {
            type: 'curved',
            curvature: curvatureForIndex(parallelIndex, parallelMaxIndex),
          });
        } else {
          graph.setEdgeAttribute(edge, 'type', 'straight');
        }
      },
    );

    graphRef.current = graph;

    const sigma = new Sigma(graph, container, {
      renderLabels: false,
      defaultNodeColor: NODE_COLOR,
      defaultEdgeColor: '#94a3b8',
      defaultEdgeType: 'straight',
      edgeProgramClasses: {
        straight: EdgeLineProgram,
        curved: EdgeCurveProgram,
      },
    });
    sigmaRef.current = sigma;

    sigma.on('clickNode', ({ node }) => onSelectNode(node));
    sigma.on('clickStage', () => onSelectNode(null));

    return () => {
      sigma.kill();
      sigmaRef.current = null;
      graphRef.current = null;
    };
  }, [nodes, edges, layers, layerColor, onSelectNode]);

  // Highlight the selected node in place rather than rebuilding the graph.
  useEffect(() => {
    const graph = graphRef.current;
    const sigma = sigmaRef.current;
    if (!graph || !sigma) return;
    graph.forEachNode((nodeId) => {
      const isSelected = nodeId === selectedNode;
      graph.setNodeAttribute(nodeId, 'color', isSelected ? SELECTED_NODE_COLOR : NODE_COLOR);
      graph.setNodeAttribute(nodeId, 'size', isSelected ? SELECTED_NODE_SIZE : NODE_SIZE);
    });
    sigma.refresh();
  }, [selectedNode]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
}