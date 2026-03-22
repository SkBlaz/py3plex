import { useState, useEffect, useCallback, useRef } from 'react';
import { Play, RefreshCw, CheckCircle, XCircle, Clock, AlertCircle, HelpCircle, Trash2 } from 'lucide-react';
import {
  computeLayout,
  computeCentrality,
  computeCommunity,
  getJobStatus,
} from '../lib/api';
import { useKeyboardShortcuts, ShortcutConfig } from '../hooks/useKeyboardShortcuts';
import ShortcutsHelp from '../components/ShortcutsHelp';
import Tooltip from '../components/Tooltip';

// Adaptive polling intervals based on job state
const POLL_INTERVALS = {
  queued: 3000,      // 3 seconds for queued jobs
  running: 2000,     // 2 seconds for running jobs  
  completed: 0,      // Stop polling for completed
  failed: 0,         // Stop polling for failed
  default: 5000      // 5 seconds default
};

export default function Analyze() {
  const [graphId, setGraphId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const prevJobsRef = useRef<any[]>([]);
  const notificationTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const storedGraphId = sessionStorage.getItem('currentGraphId') || localStorage.getItem('currentGraphId');
    if (storedGraphId) {
      setGraphId(storedGraphId);
    }
  }, []);

  // Optimized polling with adaptive intervals
  const pollJobs = useCallback(async () => {
    const activeJobs = jobs.filter(
      job => job.status === 'running' || job.status === 'queued'
    );
    
    if (activeJobs.length === 0) {
      // No active jobs, stop polling
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      return;
    }

    // Poll active jobs in batch
    const promises = activeJobs.map(async (job) => {
      try {
        const response = await getJobStatus(job.id);
        return { id: job.id, data: response.data };
      } catch (err) {
        console.error('Failed to poll job:', err);
        return null;
      }
    });

    const results = await Promise.all(promises);
    
    setJobs((prev) => {
      const updated = prev.map((j) => {
        const result = results.find(r => r?.id === j.id);
        return result ? { ...j, ...result.data } : j;
      });
      
      // Check for newly completed jobs by comparing with previous state by job ID
      updated.forEach((job) => {
        const prevJob = prevJobsRef.current.find(p => p.id === job.id);
        if (prevJob && prevJob.status !== 'completed' && job.status === 'completed') {
          // Clear any existing notification timer
          if (notificationTimerRef.current) {
            clearTimeout(notificationTimerRef.current);
          }
          setNotification(`${job.type} job completed successfully!`);
          notificationTimerRef.current = setTimeout(() => setNotification(null), 5000);
        }
      });
      
      prevJobsRef.current = updated;
      return updated;
    });

    // Schedule next poll with adaptive interval
    const minInterval = Math.min(
      ...activeJobs.map(j => POLL_INTERVALS[j.status as keyof typeof POLL_INTERVALS] || POLL_INTERVALS.default)
    );
    
    pollTimerRef.current = setTimeout(pollJobs, minInterval);
  }, [jobs]);

  useEffect(() => {
    // Start polling when jobs are added
    const hasActiveJobs = jobs.some(
      job => job.status === 'running' || job.status === 'queued'
    );
    
    if (hasActiveJobs && !pollTimerRef.current) {
      pollTimerRef.current = setTimeout(pollJobs, 2000);
    }

    return () => {
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      if (notificationTimerRef.current) {
        clearTimeout(notificationTimerRef.current);
        notificationTimerRef.current = null;
      }
    };
  }, [jobs, pollJobs]);

  const runLayoutJob = async () => {
    if (!graphId) return;
    setError(null);

    try {
      const response = await computeLayout(graphId, {
        algorithm: 'spring',
        seed: 42,
        dimensions: 2,
        iterations: 50,
      });

      setJobs((prev) => [
        ...prev,
        {
          id: response.data.job_id,
          type: 'Layout',
          status: 'queued',
          progress: 0,
        },
      ]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start layout job');
    }
  };

  const runCentralityJob = async () => {
    if (!graphId) return;
    setError(null);

    try {
      const response = await computeCentrality(graphId, {
        metrics: ['degree', 'betweenness'],
      });

      setJobs((prev) => [
        ...prev,
        {
          id: response.data.job_id,
          type: 'Centrality',
          status: 'queued',
          progress: 0,
        },
      ]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start centrality job');
    }
  };

  const runCommunityJob = async () => {
    if (!graphId) return;
    setError(null);

    try {
      const response = await computeCommunity(graphId, {
        algorithm: 'louvain',
        resolution: 1.0,
        seed: 42,
      });

      setJobs((prev) => [
        ...prev,
        {
          id: response.data.job_id,
          type: 'Community Detection',
          status: 'queued',
          progress: 0,
        },
      ]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start community detection job');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'running':
        return <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  // Clear completed jobs
  const clearCompletedJobs = () => {
    setJobs(prev => prev.filter(job => job.status !== 'completed' && job.status !== 'failed'));
  };

  // Keyboard shortcuts
  const shortcuts: ShortcutConfig[] = [
    {
      key: 'l',
      ctrl: true,
      action: runLayoutJob,
      description: 'Run layout computation'
    },
    {
      key: 'c',
      ctrl: true,
      shift: true,
      action: runCentralityJob,
      description: 'Run centrality analysis'
    },
    {
      key: 'd',
      ctrl: true,
      action: runCommunityJob,
      description: 'Run community detection'
    },
    {
      key: 'Delete',
      shift: true,
      action: clearCompletedJobs,
      description: 'Clear completed jobs'
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

  useKeyboardShortcuts(shortcuts, !!graphId);

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

  return (
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Analyze Network</h1>

      {/* Notification Banner */}
      {notification && (
        <div className="mb-6 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center justify-between animate-fade-in">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mr-2" />
            <p className="text-sm text-green-800 dark:text-green-200">{notification}</p>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
            aria-label="Close notification"
          >
            <XCircle className="h-5 w-5" />
          </button>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Layout */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Layout</h2>
            <Tooltip content="Computes node positions using force-directed algorithms for visualization">
              <HelpCircle className="h-4 w-4 text-gray-400 dark:text-gray-500 cursor-help" />
            </Tooltip>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Compute graph layout using force-directed algorithms
          </p>
          <Tooltip content="Run spring layout (Ctrl+L)">
            <button
              onClick={runLayoutJob}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center justify-center transition-colors"
            >
              <Play className="h-4 w-4 mr-2" />
              Run Spring Layout
            </button>
          </Tooltip>
        </div>

        {/* Centrality */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Centrality</h2>
            <Tooltip content="Identifies important nodes based on degree and betweenness metrics">
              <HelpCircle className="h-4 w-4 text-gray-400 dark:text-gray-500 cursor-help" />
            </Tooltip>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Compute node centrality metrics (degree, betweenness)
          </p>
          <Tooltip content="Run centrality analysis (Ctrl+Shift+C)">
            <button
              onClick={runCentralityJob}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center justify-center transition-colors"
            >
              <Play className="h-4 w-4 mr-2" />
              Run Centrality
            </button>
          </Tooltip>
        </div>

        {/* Community Detection */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Communities</h2>
            <Tooltip content="Finds groups of densely connected nodes using the Louvain algorithm">
              <HelpCircle className="h-4 w-4 text-gray-400 dark:text-gray-500 cursor-help" />
            </Tooltip>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Detect communities using Louvain algorithm
          </p>
          <Tooltip content="Run community detection (Ctrl+D)">
            <button
              onClick={runCommunityJob}
              className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center justify-center transition-colors"
            >
              <Play className="h-4 w-4 mr-2" />
              Detect Communities
            </button>
          </Tooltip>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Error</h3>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Job Center */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Job Center</h2>
          {jobs.some(j => j.status === 'completed' || j.status === 'failed') && (
            <Tooltip content="Clear completed and failed jobs (Shift+Delete)">
              <button
                onClick={clearCompletedJobs}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center transition-colors"
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Clear Done
              </button>
            </Tooltip>
          )}
        </div>

        {jobs.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">No jobs yet. Start an analysis above.</p>
            <p className="text-xs text-gray-400 dark:text-gray-500">
               Tip: Use keyboard shortcuts to quickly start jobs
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{job.type}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {job.phase || job.status}
                      {job.progress > 0 && ` (${job.progress}%)`}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400 dark:text-gray-500 font-mono">{job.id}</p>
                  {job.status === 'completed' && job.result && (
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1"> Complete</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 text-sm text-gray-500 dark:text-gray-400">
        <p>
          Jobs run asynchronously using Celery workers. Monitor detailed progress at{' '}
          <a
            href="/flower"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Flower dashboard
          </a>
          .
        </p>
      </div>

      {/* Keyboard Shortcuts Help */}
      <ShortcutsHelp shortcuts={shortcuts} />
    </div>
  );
}
