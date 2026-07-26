import { useState, useRef, useEffect } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Clock, HelpCircle } from 'lucide-react';
import { uploadFile, getGraphSummary } from '../lib/api';
import { useKeyboardShortcuts, ShortcutConfig } from '../hooks/useKeyboardShortcuts';
import ShortcutsHelp from '../components/ShortcutsHelp';
import Tooltip from '../components/Tooltip';
import LoadingProgress from '../components/LoadingProgress';

const MAX_FILE_SIZE_MB = 512;
const ACCEPTED_FORMATS = ['.txt', '.edgelist', '.gml', '.gpickle'];
const RECENT_FILES_KEY = 'py3plex-recent-files';
const MAX_RECENT_FILES = 5;

interface RecentFile {
  name: string;
  graphId: string;
  uploadedAt: string;
  nodes: number;
  edges: number;
}

export default function LoadData() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [recentFiles, setRecentFiles] = useState<RecentFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load recent files from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(RECENT_FILES_KEY);
    if (stored) {
      try {
        setRecentFiles(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse recent files:', e);
      }
    }
  }, []);

  // Save recent file
  const saveRecentFile = (fileInfo: RecentFile) => {
    // Remove duplicate if exists, add new entry at the start, limit to MAX_RECENT_FILES
    const existingIndex = recentFiles.findIndex(f => f.graphId === fileInfo.graphId);
    const updatedList = existingIndex >= 0 
      ? [fileInfo, ...recentFiles.filter((_, i) => i !== existingIndex)]
      : [fileInfo, ...recentFiles];
    
    const updated = updatedList.slice(0, MAX_RECENT_FILES);
    setRecentFiles(updated);
    localStorage.setItem(RECENT_FILES_KEY, JSON.stringify(updated));
  };

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

      // Save to recent files
      saveRecentFile({
        name: file.name,
        graphId: response.data.graph_id,
        uploadedAt: new Date().toISOString(),
        nodes: summaryResponse.data.nodes,
        edges: summaryResponse.data.edges,
      });
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

  // Load a recent file
  const loadRecentFile = (recent: RecentFile) => {
    sessionStorage.setItem('currentGraphId', recent.graphId);
    localStorage.setItem('currentGraphId', recent.graphId);
    localStorage.setItem('currentGraphName', recent.name);
    
    // Reload summary
    getGraphSummary(recent.graphId)
      .then(response => {
        setSummary(response.data);
        setUploadResult({ graph_id: recent.graphId, filename: recent.name });
      })
      .catch(() => {
        setError('Failed to load recent file. It may have been deleted.');
      });
  };

  // Keyboard shortcuts
  const shortcuts: ShortcutConfig[] = [
    {
      key: 'u',
      ctrl: true,
      action: () => fileInputRef.current?.click(),
      description: 'Open file picker'
    },
    {
      key: 'Enter',
      ctrl: true,
      action: () => {
        if (file && !uploading) {
          handleUpload();
        }
      },
      description: 'Upload selected file'
    },
    {
      key: 'Escape',
      action: () => {
        setFile(null);
        setError(null);
        setValidationError(null);
      },
      description: 'Clear selection and errors'
    },
    {
      key: '/',
      ctrl: true,
      action: () => {
        // Handled by ShortcutsHelp component
      },
      description: 'Show keyboard shortcuts'
    }
  ];

  useKeyboardShortcuts(shortcuts);

  return (
    <div className="px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Load Network Data</h1>
        <Tooltip content="Upload network files for analysis and visualization">
          <HelpCircle className="h-5 w-5 text-gray-400 dark:text-gray-500" />
        </Tooltip>
      </div>

      {/* Recent Files */}
      {recentFiles.length > 0 && !uploadResult && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <Clock className="h-5 w-5 mr-2 text-gray-600 dark:text-gray-400" />
            Recent Files
          </h2>
          <div className="space-y-2">
            {recentFiles.map((recent, index) => (
              <button
                key={index}
                onClick={() => loadRecentFile(recent)}
                className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg text-left transition-colors"
              >
                <div className="flex items-center flex-1">
                  <FileText className="h-5 w-5 text-gray-400 dark:text-gray-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{recent.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {recent.nodes} nodes, {recent.edges} edges • {new Date(recent.uploadedAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">Load →</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* File Upload Area */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center hover:border-blue-500 dark:hover:border-blue-400 transition"
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
          <div className="mb-4">
            <label htmlFor="file-upload" className="cursor-pointer">
              <span className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
                Click to upload
              </span>
              <span className="text-gray-600 dark:text-gray-400"> or drag and drop</span>
            </label>
            <input
              ref={fileInputRef}
              id="file-upload"
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".txt,.edgelist,.gml,.gpickle"
            />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Supported formats: .txt, .edgelist, .gml, .gpickle
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
             Tip: Press <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">Ctrl+U</kbd> to open file picker
          </p>
        </div>

        {file && (
          <div className="mt-4 flex items-center justify-between bg-gray-50 dark:bg-gray-700 p-4 rounded">
            <div className="flex items-center flex-1">
              <FileText className="h-6 w-6 text-gray-400 dark:text-gray-500 mr-2" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{file.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(file.size)}</p>
              </div>
            </div>
            <Tooltip content="Upload the selected file (Ctrl+Enter)">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? 'Uploading...' : 'Upload & Parse'}
              </button>
            </Tooltip>
          </div>
        )}

        {validationError && (
          <div className="mt-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Validation Error</h3>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">{validationError}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Upload Error</h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Upload Progress Indicator */}
      {uploading && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <LoadingProgress 
            message="Uploading and parsing network file..."
          />
          <p className="text-center text-sm text-gray-600 dark:text-gray-400 mt-4">
            This may take a moment for large files
          </p>
        </div>
      )}

      {/* Summary */}
      {summary && uploadResult && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <div className="flex items-center mb-4">
            <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400 mr-2" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Network Summary</h2>
          </div>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Graph ID</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 font-mono">{uploadResult?.graph_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Filename</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{uploadResult?.filename}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Nodes</dt>
              <dd className="mt-1 text-2xl font-bold text-blue-600 dark:text-blue-400">{summary.nodes}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Edges</dt>
              <dd className="mt-1 text-2xl font-bold text-blue-600 dark:text-blue-400">{summary.edges}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Layers</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 max-h-24 overflow-y-auto pr-1 scrollbar-visible">
                {summary.layers.join(', ') || 'N/A'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Attributes</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
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
      <div className="mt-6 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-2">Accepted Data Formats</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• <strong>Edge list (.txt, .edgelist):</strong> node1 node2 [layer] [weight]</li>
          <li>• <strong>GML (.gml):</strong> Graph Modeling Language format</li>
          <li>• <strong>Pickle (.gpickle):</strong> NetworkX pickled graph</li>
        </ul>
        <p className="text-sm text-blue-700 dark:text-blue-300 mt-3">
          <strong>Note:</strong> Maximum file size is {MAX_FILE_SIZE_MB}MB. Comments starting with # are supported in edgelist files.
        </p>
      </div>

      {/* Keyboard Shortcuts Help */}
      <ShortcutsHelp shortcuts={shortcuts} />
    </div>
  );
}
