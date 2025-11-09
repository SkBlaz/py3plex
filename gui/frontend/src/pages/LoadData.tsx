import { useState } from 'react';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { uploadFile, getGraphSummary } from '../lib/api';

export default function LoadData() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const response = await uploadFile(file);
      setUploadResult(response.data);

      // Fetch summary
      const summaryResponse = await getGraphSummary(response.data.graph_id);
      setSummary(summaryResponse.data);

      // Store graph ID in sessionStorage for other pages
      sessionStorage.setItem('currentGraphId', response.data.graph_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Load Network Data</h1>

      {/* File Upload Area */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition"
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <div className="mb-4">
            <label htmlFor="file-upload" className="cursor-pointer">
              <span className="text-blue-600 hover:text-blue-700 font-medium">
                Click to upload
              </span>
              <span className="text-gray-600"> or drag and drop</span>
            </label>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".txt,.edgelist,.gml,.gpickle"
            />
          </div>
          <p className="text-sm text-gray-500">
            Supported formats: .txt, .edgelist, .gml, .gpickle
          </p>
        </div>

        {file && (
          <div className="mt-4 flex items-center justify-between bg-gray-50 p-4 rounded">
            <div className="flex items-center">
              <FileText className="h-6 w-6 text-gray-400 mr-2" />
              <span className="text-sm font-medium text-gray-900">{file.name}</span>
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {uploading ? 'Uploading...' : 'Upload & Parse'}
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      {summary && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Network Summary</h2>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Graph ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{uploadResult?.graph_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Filename</dt>
              <dd className="mt-1 text-sm text-gray-900">{uploadResult?.filename}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Nodes</dt>
              <dd className="mt-1 text-2xl font-bold text-blue-600">{summary.nodes}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Edges</dt>
              <dd className="mt-1 text-2xl font-bold text-blue-600">{summary.edges}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Layers</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {summary.layers.join(', ') || 'N/A'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Attributes</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {summary.attributes.join(', ') || 'None'}
              </dd>
            </div>
          </dl>

          <div className="mt-6">
            <a
              href="/visualize"
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-block"
            >
              Visualize Network →
            </a>
          </div>
        </div>
      )}

      {/* Format Help */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">Accepted Data Formats</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Edge list (.txt, .edgelist):</strong> node1 node2 [layer] [weight]</li>
          <li>• <strong>GML (.gml):</strong> Graph Modeling Language format</li>
          <li>• <strong>Pickle (.gpickle):</strong> NetworkX pickled graph</li>
        </ul>
      </div>
    </div>
  );
}
