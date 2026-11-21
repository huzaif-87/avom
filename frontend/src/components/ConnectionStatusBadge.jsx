import React from 'react';
import { RefreshCw } from 'lucide-react';

export default function ConnectionStatusBadge({
  status,
  onRefresh,
  isRefreshing,
}) {
  const isConnected = status?.connected === true;
  const isLoading = status?.loading || isRefreshing;

  return (
    <div className="flex items-center gap-2">
      <div
        className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
          isLoading
            ? 'bg-cream-200 text-charcoal border-sage-muted'
            : isConnected
            ? 'bg-olive-light text-olive-dark border-sage/60'
            : 'bg-terracotta-light text-terracotta-dark border-terracotta/40'
        }`}
        title={
          isConnected
            ? `Backend connected (FastAPI v${status.version || '1.0.0'} • ${status.latencyMs ?? 0}ms)`
            : 'Backend offline: Check FastAPI server on port 8000'
        }
      >
        <span className="relative flex h-2 w-2">
          {isConnected && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-olive opacity-50"></span>
          )}
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${
              isLoading
                ? 'bg-sage animate-pulse'
                : isConnected
                ? 'bg-olive'
                : 'bg-terracotta'
            }`}
          />
        </span>

        <span className="text-[11px] font-medium leading-none">
          {isLoading
            ? 'Checking'
            : isConnected
            ? 'Connected'
            : 'Offline'}
        </span>

        {!isConnected && onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="p-0.5 rounded text-terracotta-dark hover:text-charcoal transition-colors disabled:opacity-50"
            title="Retry connection"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>
    </div>
  );
}
