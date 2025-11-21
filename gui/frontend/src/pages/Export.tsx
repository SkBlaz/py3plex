import { useState, useEffect } from 'react';
import { Download, Package, AlertCircle, CheckCircle } from 'lucide-react';
import { saveWorkspace } from '../lib/api';
import api from '../lib/api';

export default function Export() {
  const [graphId, setGraphId] = useState<string | null>(null);
  const [workspaceName, setWorkspaceName] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<any>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    const storedGraphId = sessionStorage.getItem('currentGraphId') || localStorage.getItem('currentGraphId');
    if (storedGraphId) {
      setGraphId(storedGraphId);
    }
  }, []);

  const handleDownload = async (type: string, filename: string) => {
    if (!graphId) return;
    
    setDownloading(type);
    setDownloadError(null);
    
    try {
      let endpoint = '';
      let contentType = '';
      
      switch (type) {
        case 'centrality':
          endpoint = `/graphs/${graphId}/analysis/centrality/export`;
          contentType = 'text/csv';
          break;
        case 'community':
          endpoint = `/graphs/${graphId}/analysis/community/export`;
          contentType = 'application/json';
          break;
        case 'positions':
          endpoint = `/graphs/${graphId}/positions/export`;
          contentType = 'application/json';
          break;
        default:
          throw new Error('Unknown export type');
      }
      
      const response = await api.get(endpoint, {
        responseType: 'blob',
      });
      
      // Validate response data
      if (!response.data) {
        throw new Error('No data received from server');
      }
      
      // Create download link with proper cleanup
      const blob = new Blob([response.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      
      try {
        link.click();
      } finally {
        // Always cleanup, even if click fails
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        setDownloadError(`No ${type} data available. Please run the corresponding analysis first.`);
      } else {
        setDownloadError(err.response?.data?.detail || `Failed to download ${type} data`);
      }
    } finally {
      setDownloading(null);
    }
  };

  const handleSaveWorkspace = async () => {
    if (!graphId || !workspaceName) return;

    setSaving(true);
    setSaveError(null);
    setSaveResult(null);

    try {
      const response = await saveWorkspace({
        name: workspaceName,
        graph_id: graphId,
        view_state: {},
      });
      setSaveResult(response.data);
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || 'Failed to save workspace');
    } finally {
      setSaving(false);
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
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Export & Download</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Export Options */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Export Options</h2>

          {downloadError && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded p-3 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{downloadError}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Download Results</h3>
              <div className="space-y-2">
                <button 
                  onClick={() => handleDownload('centrality', `centrality-${graphId}.csv`)}
                  disabled={downloading === 'centrality'}
                  className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center justify-center text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {downloading === 'centrality' ? 'Downloading...' : 'Download Centrality CSV'}
                </button>
                <button 
                  onClick={() => handleDownload('community', `community-${graphId}.json`)}
                  disabled={downloading === 'community'}
                  className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center justify-center text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {downloading === 'community' ? 'Downloading...' : 'Download Community JSON'}
                </button>
                <button 
                  onClick={() => handleDownload('positions', `positions-${graphId}.json`)}
                  disabled={downloading === 'positions'}
                  className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center justify-center text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {downloading === 'positions' ? 'Downloading...' : 'Download Layout Positions'}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Note: Data must be computed in the Analyze page before downloading
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Visualization Export
              </h3>
              <button className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center justify-center text-sm">
                <Download className="h-4 w-4 mr-2" />
                Export Snapshot (PNG)
              </button>
            </div>
          </div>
        </div>

        {/* Workspace Save */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Save Workspace</h2>
          <p className="text-sm text-gray-600 mb-4">
            Package your data, parameters, and view state into a reloadable bundle
          </p>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Workspace Name
            </label>
            <input
              type="text"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              placeholder="my-network-workspace"
              className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            onClick={handleSaveWorkspace}
            disabled={saving || !workspaceName}
            className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            <Package className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Workspace Bundle'}
          </button>

          {saveError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded p-3">
              <p className="text-sm text-red-700">{saveError}</p>
            </div>
          )}

          {saveResult && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded p-3 flex items-start">
              <CheckCircle className="h-5 w-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-green-700">
                  ✓ Workspace saved as <strong>{saveResult.filename}</strong>
                </p>
                <p className="text-xs text-green-600 mt-1">
                  ID: {saveResult.workspace_id}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">About Workspaces</h3>
        <p className="text-sm text-blue-800">
          Workspace bundles include your uploaded data, computed results, and UI state.
          Load them later to resume your analysis session without re-uploading or
          re-computing.
        </p>
      </div>
    </div>
  );
}
