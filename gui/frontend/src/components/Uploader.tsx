/**
 * Uploader - File Upload Component
 * 
 * PURPOSE: Handle network file uploads
 * STATUS: Functionality integrated directly into LoadData page
 * 
 * CURRENT IMPLEMENTATION:
 * - This file is a stub/redirect
 * - Actual implementation: pages/LoadData.tsx (lines 50-150 approx)
 * - Upload logic in: lib/api.ts (uploadFile function)
 * 
 * RATIONALE FOR INLINE IMPLEMENTATION:
 * - Upload is tightly coupled with format selection and preview
 * - Better UX to have everything on one page
 * - Drag-and-drop integrated with file browser in same component
 * 
 * IF NEEDED AS SEPARATE COMPONENT:
 * - Extract upload area from LoadData.tsx
 * - Props: onUploadComplete, acceptedFormats, maxSize
 * - Features: drag-drop, progress bar, file validation
 * - Would allow reuse in workspace restore, export, etc.
 * 
 * CURRENT FILE FORMATS SUPPORTED:
 * - .edgelist, .multiedgelist (multi-layer networks)
 * - .gml (Graph Modelling Language)
 * - .gpickle (NetworkX pickle format)
 * - See: api/app/services/io.py for parsers
 */

// Export empty object to satisfy TypeScript module requirements
export {}
