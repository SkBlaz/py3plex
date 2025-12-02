import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { Toast, ToastType } from '../hooks/useToasts';

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

const toastStyles: Record<ToastType, { bg: string; icon: React.ReactNode; border: string }> = {
  success: {
    bg: 'bg-green-50 dark:bg-green-900/30',
    border: 'border-green-200 dark:border-green-800',
    icon: <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />,
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-900/30',
    border: 'border-red-200 dark:border-red-800',
    icon: <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />,
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/30',
    border: 'border-yellow-200 dark:border-yellow-800',
    icon: <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />,
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-900/30',
    border: 'border-blue-200 dark:border-blue-800',
    icon: <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />,
  },
};

/**
 * Toast container - displays toast notifications in the bottom-right corner
 */
export default function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => {
        const style = toastStyles[toast.type];
        
        return (
          <div
            key={toast.id}
            className={`${style.bg} ${style.border} border rounded-lg shadow-lg p-4 flex items-start gap-3 animate-slide-in`}
            role="alert"
          >
            {style.icon}
            <p className="flex-1 text-sm text-gray-900 dark:text-gray-100">
              {toast.message}
            </p>
            <button
              onClick={() => onRemove(toast.id)}
              className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
