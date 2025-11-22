import { useState } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { uploadFile, getGraphSummary } from '../lib/api';

const MAX_FILE_SIZE_MB = 512;
const ACCEPTED_FORMATS = ['.txt', '.edgelist', '.gml', '.gpickle'];

export default function LoadData() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_FILE_SIZE_MB) {
      return `File size (${fileSizeMB.toFixed(1)}MB) exceeds maximum allowed size of ${MAX_FILE_SIZE_MB}MB`;
    }

    // Check file extension - use lastIndexOf to handle filenames with multiple dots
    const lastDotIndex = file.name.lastIndexOf('.');
    if (lastDotIndex === -1 || lastDotIndex === file.name.length - 1) {
      return `File has no extension. Please use: ${ACCEPTED_FORMATS.join(', ')}`;
    }
    const extension = file.name.substring(lastDotIndex).toLowerCase();
    if (!ACCEPTED_FORMATS.includes(extension)) {
      return `File format ${extension} is not supported. Please use: ${ACCEPTED_FORMATS.join(', ')}`;
    }

    return null;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const validation = validateFile(selectedFile);
      
      if (validation) {
        setValidationError(validation);
        setFile(null);
      } else {
        setFile(selectedFile);
        setValidationError(null);
      }
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

      // Store graph ID in both sessionStorage and localStorage for persistence
      sessionStorage.setItem('currentGraphId', response.data.graph_id);
      localStorage.setItem('currentGraphId', response.data.graph_id);
      localStorage.setItem('currentGraphName', file.name);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const validation = validateFile(droppedFile);
      
      if (validation) {
        setValidationError(validation);
        setFile(null);
      } else {
        setFile(droppedFile);
        setValidationError(null);
      }
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
            <div className="flex items-center flex-1">
              <FileText className="h-6 w-6 text-gray-400 mr-2" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
              </div>
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {uploading ? 'Uploading...' : 'Upload & Parse'}
            </button>
          </div>
        )}

        {validationError && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">Validation Error</h3>
              <p className="text-sm text-yellow-700 mt-1">{validationError}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Upload Progress Indicator */}
      {uploading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <div>
              <p className="text-blue-900 font-medium">Uploading and parsing network file...</p>
              <p className="text-blue-700 text-sm mt-1">This may take a moment for large files</p>
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      {summary && uploadResult && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center mb-4">
            <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-xl font-bold text-gray-900">Network Summary</h2>
          </div>
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

          <div className="mt-6 flex gap-3">
            <a
              href="/visualize"
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-block transition-colors"
            >
              Visualize Network →
            </a>
            <a
              href="/analyze"
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 inline-block transition-colors"
            >
              Analyze Network →
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
        <p className="text-sm text-blue-700 mt-3">
          <strong>Note:</strong> Maximum file size is {MAX_FILE_SIZE_MB}MB. Comments starting with # are supported in edgelist files.
        </p>
      </div>
    </div>
  );
}
