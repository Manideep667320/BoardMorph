import React, { useState } from 'react';
import {
  Layers,
  Play,
  ShieldAlert,
  Loader2,
  RefreshCw,
  ExternalLink,
  Settings,
  X,
  Radio,
  CheckCircle2,
} from 'lucide-react';

interface HeaderProps {
  boardId: string;
  hasToken: boolean;
  isLiveSyncActive: boolean;
  onToggleLiveSync: () => void;
  onSyncNow: () => Promise<void>;
  onUpdateConfig: (boardId: string, accessToken?: string) => Promise<void>;
  onRun: () => void;
  onBreak: () => void;
  isRunning: boolean;
  isSyncing: boolean;
  vulnerabilityCount: number;
  lastSyncedAt: Date | null;
}

export const Header: React.FC<HeaderProps> = ({
  boardId,
  hasToken,
  isLiveSyncActive,
  onToggleLiveSync,
  onSyncNow,
  onUpdateConfig,
  onRun,
  onBreak,
  isRunning,
  isSyncing,
  vulnerabilityCount,
  lastSyncedAt,
}) => {
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [inputBoardId, setInputBoardId] = useState(boardId);
  const [inputToken, setInputToken] = useState('');
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  const cleanBoardId = boardId ? boardId.replace(/^https?:\/\/.*(?:board|welcomeonboard)\//, '').replace(/[/?#].*$/, '') : '';
  const miroBoardUrl = cleanBoardId ? `https://miro.com/app/board/${cleanBoardId}/` : 'https://miro.com';

  const handleOpenModal = () => {
    setInputBoardId(boardId);
    setInputToken('');
    setShowConfigModal(true);
  };

  const handleConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputBoardId.trim()) return;
    setIsSavingConfig(true);
    try {
      await onUpdateConfig(inputBoardId.trim(), inputToken.trim() || undefined);
      setShowConfigModal(false);
    } catch (err: any) {
      alert(`Failed to save Miro configuration: ${err.message}`);
    } finally {
      setIsSavingConfig(false);
    }
  };

  return (
    <>
      <header className="fixed top-0 left-0 right-0 w-full h-16 flex items-center justify-between px-6 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-xs">
        {/* Left Cluster: Brand & Miro Live Status */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-emerald-500 flex items-center justify-center shadow-xs text-white">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-slate-900">
                  BoardMorph
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium border border-slate-200">
                  Miro × Qwen
                </span>
              </div>
            </div>
          </div>

          {/* Miro Board Live Connection Indicator */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleOpenModal}
              title="Configure Miro Board & Token"
              className="group flex items-center space-x-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-slate-300 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
            >
              <div className="w-2 h-2 rounded-full relative">
                {hasToken ? (
                  <>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </>
                ) : (
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                )}
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-semibold text-slate-700">Miro Board:</span>
                <span className="text-xs font-mono text-slate-500 max-w-[140px] truncate">
                  {cleanBoardId || 'Not connected'}
                </span>
              </div>
              <Settings className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 transition-colors" />
            </button>

            {cleanBoardId && (
              <a
                href={miroBoardUrl}
                target="_blank"
                rel="noreferrer"
                title="Open board in Miro"
                className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>

          {/* Real-time Live Sync Toggle */}
          <div className="hidden md:flex items-center space-x-2">
            <button
              onClick={onToggleLiveSync}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all ${
                isLiveSyncActive
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                  : 'bg-slate-100 text-slate-500 border-slate-200 hover:bg-slate-200'
              }`}
              title={isLiveSyncActive ? 'Click to pause live sync' : 'Click to resume real-time sync'}
            >
              <Radio
                className={`w-3.5 h-3.5 ${
                  isLiveSyncActive ? 'text-emerald-500 animate-pulse' : 'text-slate-400'
                }`}
              />
              <span>{isLiveSyncActive ? 'Live Sync: Active' : 'Live Sync: Paused'}</span>
            </button>

            {/* Sync Now Action */}
            <button
              onClick={() => onSyncNow()}
              disabled={isSyncing}
              className="flex items-center space-x-1 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:border-slate-300 px-2 py-1 rounded-md transition-colors disabled:opacity-50"
              title="Force sync board now"
            >
              <RefreshCw className={`w-3 h-3 text-slate-500 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
            </button>

            {lastSyncedAt && (
              <span className="text-[11px] text-slate-400 font-medium">
                {lastSyncedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            )}
          </div>
        </div>

        {/* Right Cluster: Actions */}
        <div className="flex items-center space-x-3">
          {/* Break My Agent Audit Trigger */}
          <button
            onClick={onBreak}
            disabled={isRunning}
            className="flex items-center space-x-2 px-3.5 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg font-medium text-sm shadow-xs hover:shadow-md hover:from-amber-600 hover:to-orange-600 transition-all active:scale-95 disabled:opacity-50"
          >
            <ShieldAlert className="w-4 h-4 text-white" />
            <span>Break My Agent</span>
            {vulnerabilityCount > 0 && (
              <span className="ml-1 px-1.5 py-0.2 bg-white/20 rounded-full text-xs font-bold text-white">
                {vulnerabilityCount}
              </span>
            )}
          </button>

          {/* Run Workflow CTA */}
          <button
            onClick={onRun}
            disabled={isRunning}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium text-sm shadow-xs hover:shadow-md hover:from-emerald-700 hover:to-teal-700 transition-all active:scale-95 disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 text-white fill-white" />
                <span>Run Workflow</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Miro Connection & Setup Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg p-6 relative">
            <button
              onClick={() => setShowConfigModal(false)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                <Radio className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Miro Live Sync Settings</h3>
                <p className="text-xs text-slate-500">
                  Real-time two-way synchronization between your Miro canvas and BoardMorph
                </p>
              </div>
            </div>

            <form onSubmit={handleConfigSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Miro Board URL or Board ID
                </label>
                <input
                  type="text"
                  required
                  placeholder="https://miro.com/app/board/uXjV...=/ or uXjV..."
                  value={inputBoardId}
                  onChange={(e) => setInputBoardId(e.target.value)}
                  className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Copy the full link directly from your browser's address bar on Miro.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Miro App Access Token
                </label>
                <input
                  type="password"
                  placeholder={hasToken ? '•••••••••••••••••••••••• (Configured)' : 'eyJhbGciOi...'}
                  value={inputToken}
                  onChange={(e) => setInputToken(e.target.value)}
                  className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  In your Miro App at{' '}
                  <a
                    href="https://developers.miro.com/"
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline font-medium inline-flex items-center space-x-0.5"
                  >
                    <span>developers.miro.com</span>
                    <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                  </a>{' '}
                  under <span className="font-semibold text-slate-600">Install app and get OAuth token</span> (requires <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-600 font-mono">boards:read</code> and <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-600 font-mono">boards:write</code>).
                </p>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2 text-xs text-slate-600">
                <div className="font-semibold text-slate-800 flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>How Real-Time Sync Works:</span>
                </div>
                <ul className="list-disc list-inside space-y-1 text-slate-500 text-[11px]">
                  <li>Every change made in Miro triggers an automatic hash diff within ~2.5s.</li>
                  <li>Qwen recompiles the graph on the fly, rendering live on your canvas.</li>
                  <li>"Break My Agent" warnings write directly back to Miro as red sticky notes!</li>
                </ul>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowConfigModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingConfig || !inputBoardId.trim()}
                  className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                >
                  {isSavingConfig ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving & Connecting...</span>
                    </>
                  ) : (
                    <span>Save & Start Live Sync</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
