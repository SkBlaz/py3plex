import { Loader2 } from 'lucide-react';

interface LoadingProgressProps {
  message?: string;
  progress?: number;
  showSpinner?: boolean;
}

/**
 * Loading progress indicator with optional progress bar
 * 
 * @param message - Loading message to display
 * @param progress - Progress percentage (0-100), if undefined shows indeterminate
 * @param showSpinner - Whether to show spinner animation (default: true)
 */
export default function LoadingProgress({ 
  message = 'Loading...', 
  progress,
  showSpinner = true 
}: LoadingProgressProps) {
  const hasProgress = progress !== undefined;
  const progressPercent = hasProgress ? Math.min(Math.max(progress, 0), 100) : 0;

  return (
    <div className="flex flex-col items-center justify-center py-8">
      {showSpinner && (
        <Loader2 className="h-8 w-8 text-blue-600 dark:text-blue-400 animate-spin mb-4" />
      )}
      
      <p className="text-gray-900 dark:text-gray-100 font-medium mb-2">{message}</p>
      
      {hasProgress ? (
        <div className="w-64 mt-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-600 dark:text-gray-400">Progress</span>
            <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="w-64 mt-4">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
            <div className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '40%' }} />
          </div>
        </div>
      )}
    </div>
  );
}
