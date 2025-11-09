import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health
export const healthCheck = () => api.get('/health');

// Upload
export const uploadFile = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Graphs
export const getGraphSummary = (graphId: string) =>
  api.get(`/graphs/${graphId}/summary`);

export const filterGraph = (graphId: string, spec: any) =>
  api.post(`/graphs/${graphId}/filter`, spec);

export const getGraphPositions = (graphId: string) =>
  api.get(`/graphs/${graphId}/positions`);

export const sampleGraph = (graphId: string, maxNodes: number = 500) =>
  api.get(`/graphs/${graphId}/sample`, { params: { max_nodes: maxNodes } });

// Analysis
export const computeLayout = (graphId: string, request: any) =>
  api.post(`/graphs/${graphId}/layout`, request);

export const computeCentrality = (graphId: string, request: any) =>
  api.post(`/graphs/${graphId}/analysis/centrality`, request);

export const computeCommunity = (graphId: string, request: any) =>
  api.post(`/graphs/${graphId}/analysis/community`, request);

// Jobs
export const getJobStatus = (jobId: string) => api.get(`/jobs/${jobId}`);

export const cancelJob = (jobId: string) => api.delete(`/jobs/${jobId}`);

// Workspace
export const saveWorkspace = (request: any) =>
  api.post('/workspaces/save', request);

export const loadWorkspace = (workspaceId: string) =>
  api.post('/workspaces/load', { workspace_id: workspaceId });

export default api;
