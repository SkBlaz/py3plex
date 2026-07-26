// react-cytoscapejs ships no type declarations of its own (and no
// well-maintained @types package exists for it), so this is a minimal
// shim covering only the props this project actually uses.
declare module 'react-cytoscapejs' {
  import type { Component, CSSProperties } from 'react';
  import type cytoscape from 'cytoscape';

  export interface CytoscapeComponentProps {
    elements: cytoscape.ElementDefinition[];
    style?: CSSProperties;
    layout?: cytoscape.LayoutOptions;
    stylesheet?: cytoscape.StylesheetStyle[];
    cy?: (cy: cytoscape.Core) => void;
    className?: string;
  }

  export default class CytoscapeComponent extends Component<CytoscapeComponentProps> {}
}