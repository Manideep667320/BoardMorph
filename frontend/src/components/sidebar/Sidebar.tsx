import React, { useState, useEffect } from 'react';
import {
  Receipt,
  Settings,
  Shield,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Cpu,
  Coins,
  Wrench,
  Sparkles,
  Share2,
} from 'lucide-react';
import type {
  CompiledNode,
  ExecutableAgentSpec,
  HealthReport,
  StepTrace,
  Vulnerability,
} from '../../types/agent';

interface SidebarProps {
  spec: ExecutableAgentSpec | null;
  userInput: string;
  setUserInput: (val: string) => void;
  isRunning: boolean;
  onRun: () => void;
  traces: StepTrace[];
  finalOutput: any;
  selectedNode: CompiledNode | null;
  healthReport: HealthReport | null;
  onApplyFix: (vuln: Vulnerability) => void;
  onWriteAuditToMiro?: (content: string) => Promise<void>;
  onWriteFixToMiro?: (title: string) => Promise<void>;
}

export const Sidebar: React.FC<SidebarProps> = ({
  userInput,
  setUserInput,
  isRunning,
  onRun,
  traces,
  finalOutput,
  selectedNode,
  healthReport,
  onApplyFix,
  onWriteAuditToMiro,
  onWriteFixToMiro,
}) => {
  const [activeTab, setActiveTab] = useState<'trace' | 'inspector' | 'break'>('trace');
  const [isStreaming, setIsStreaming] = useState(true);
  const [isWritingToMiro, setIsWritingToMiro] = useState(false);

  useEffect(() => {
    if (isRunning) {
      setActiveTab('trace');
    }
  }, [isRunning]);

  const vulnerabilityCount = healthReport?.vulnerabilities.length || 0;

  const handleWriteMiroNote = async (text: string) => {
    if (!onWriteAuditToMiro) return;
    setIsWritingToMiro(true);
    try {
      await onWriteAuditToMiro(text);
      alert('⚠️ Audit warning sticky note written to Miro board via Miro App API!');
    } catch (e: any) {
      alert(`Miro write failed: ${e.message}`);
    } finally {
      setIsWritingToMiro(false);
    }
  };

  const handleWriteMiroFix = async (title: string) => {
    if (!onWriteFixToMiro) return;
    setIsWritingToMiro(true);
    try {
      await onWriteFixToMiro(title);
      alert('✅ Fix guardrail shape created on Miro board via Miro App API!');
    } catch (e: any) {
      alert(`Miro fix placement failed: ${e.message}`);
    } finally {
      setIsWritingToMiro(false);
    }
  };

  return (
    <aside className="w-[420px] bg-white border-l border-slate-200 flex flex-col h-[calc(100vh-64px)] z-30 shadow-xs">
      {/* Tab Strip */}
      <div className="flex border-b border-slate-200 px-4 pt-3 space-x-4 bg-white shrink-0">
        <button
          onClick={() => setActiveTab('trace')}
          className={`pb-3 text-sm font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'trace'
              ? 'text-blue-600 border-blue-600'
              : 'text-slate-500 border-transparent hover:text-slate-900'
          }`}
        >
          <Receipt className="w-4 h-4" />
          <span>Execution Trace</span>
        </button>

        <button
          onClick={() => setActiveTab('inspector')}
          className={`pb-3 text-sm font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'inspector'
              ? 'text-blue-600 border-blue-600'
              : 'text-slate-500 border-transparent hover:text-slate-900'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Node Inspector</span>
        </button>

        <button
          onClick={() => setActiveTab('break')}
          className={`pb-3 text-sm font-semibold flex items-center space-x-1.5 transition-colors cursor-pointer border-b-2 ${
            activeTab === 'break'
              ? 'text-amber-600 border-amber-500'
              : 'text-slate-500 border-transparent hover:text-slate-900'
          }`}
        >
          <Shield className="w-4 h-4 text-amber-500" />
          <span>Break Report</span>
          {vulnerabilityCount > 0 && (
            <span className="w-4 h-4 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold flex items-center justify-center">
              {vulnerabilityCount}
            </span>
          )}
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Trigger Query Box (always accessible on top) */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-800 flex items-center space-x-1.5">
              <Play className="w-3.5 h-3.5 text-blue-600 fill-current" />
              <span>Test Prompt / Trigger Query</span>
            </label>
            <div className="flex items-center space-x-1.5 text-xs text-slate-500">
              <span>Streaming</span>
              <button
                type="button"
                onClick={() => setIsStreaming(!isStreaming)}
                className={`w-7 h-4 rounded-full relative p-0.5 cursor-pointer transition-colors ${
                  isStreaming ? 'bg-emerald-500' : 'bg-slate-300'
                }`}
              >
                <div
                  className={`w-3 h-3 bg-white rounded-full shadow-xs transform transition-transform ${
                    isStreaming ? 'translate-x-3' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>

          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            disabled={isRunning}
            rows={2}
            className="w-full text-sm p-2.5 bg-slate-50 rounded-lg border border-slate-200 focus:ring-1 focus:ring-blue-600 focus:border-blue-600 text-slate-800 resize-none outline-none leading-relaxed"
            placeholder="Enter user query to test agent workflow..."
          />

          <div className="flex justify-end">
            <button
              onClick={() => {
                setActiveTab('trace');
                onRun();
              }}
              disabled={isRunning || !userInput.trim()}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-semibold transition-colors cursor-pointer active:scale-95 disabled:opacity-50"
            >
              {isRunning ? (
                <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 text-blue-600 fill-current" />
              )}
              <span>{isRunning ? 'Running Trace...' : 'Run Test Step'}</span>
            </button>
          </div>
        </div>

        {/* TAB 1: EXECUTION TRACE */}
        {activeTab === 'trace' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Live Workflow Trace</h3>
              <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                {traces.length > 0 ? `${traces.length} Steps Logged` : 'Ready to Run'}
              </span>
            </div>

            {/* Checklist of steps */}
            <div className="space-y-2">
              {traces.length === 0 ? (
                <div className="text-center py-8 px-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                  Click <span className="font-semibold text-slate-600">"Run Flow"</span> or <span className="font-semibold text-slate-600">"Run Test Step"</span> to observe real-time execution across nodes.
                </div>
              ) : (
                traces.map((trace, i) => (
                  <div
                    key={trace.step_number || i}
                    className={`flex items-start space-x-3 p-3 rounded-lg border transition-all ${
                      trace.status === 'completed'
                        ? 'bg-slate-50/80 border-slate-200'
                        : trace.status === 'failed'
                        ? 'bg-rose-50 border-rose-200'
                        : 'bg-white border-2 border-emerald-400 shadow-xs'
                    }`}
                  >
                    {trace.status === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                    ) : trace.status === 'failed' ? (
                      <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
                    ) : (
                      <Loader2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0 animate-spin" />
                    )}

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-900 truncate">
                          {trace.node_label}
                        </span>
                        <span className="text-xs font-mono text-slate-400">
                          {trace.duration_ms ? `${Math.round(trace.duration_ms)}ms` : 'active'}
                        </span>
                      </div>

                      {trace.output_payload && (
                        <div className="mt-1 text-[11px] font-mono text-slate-600 bg-white p-1.5 rounded border border-slate-200 max-h-24 overflow-y-auto">
                          {typeof trace.output_payload === 'string'
                            ? trace.output_payload
                            : JSON.stringify(trace.output_payload, null, 2)}
                        </div>
                      )}

                      {trace.error_message && (
                        <p className="mt-1 text-xs text-rose-600 font-medium">
                          {trace.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Final Answer Banner */}
            {finalOutput && (
              <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-2">
                <div className="flex items-center space-x-2 text-emerald-800 font-bold text-xs">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <span>Agent Deliverable / Final Output</span>
                </div>
                <div className="text-sm text-slate-800 leading-relaxed font-normal bg-white p-3 rounded-lg border border-emerald-100 whitespace-pre-wrap">
                  {typeof finalOutput === 'string'
                    ? finalOutput
                    : JSON.stringify(finalOutput, null, 2)}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: NODE INSPECTOR */}
        {activeTab === 'inspector' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Node Configuration</h3>
            {selectedNode ? (
              <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-3">
                <div>
                  <span className="text-xs text-slate-400 uppercase font-semibold">Node ID</span>
                  <p className="text-sm font-mono text-slate-800 font-medium">{selectedNode.id}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase font-semibold">Type</span>
                  <p className="text-sm text-slate-800 font-medium uppercase">{selectedNode.type}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase font-semibold">Description</span>
                  <p className="text-sm text-slate-700 leading-relaxed">{selectedNode.description}</p>
                </div>

                {selectedNode.config && Object.keys(selectedNode.config).length > 0 && (
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-semibold">Config Parameters</span>
                    <pre className="text-xs font-mono bg-white p-2.5 rounded-lg border border-slate-200 text-slate-800 overflow-x-auto mt-1">
                      {JSON.stringify(selectedNode.config, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 px-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                Click on any node on the canvas to inspect its compiled configuration, prompt templates, and routing logic.
              </div>
            )}
          </div>
        )}

        {/* TAB 3: BREAK REPORT */}
        {activeTab === 'break' && (
          <div className="space-y-4">
            {healthReport ? (
              <div className="space-y-4">
                {/* Health Score Gauge */}
                <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
                      <Shield className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Agent Health Score</h4>
                      <p className="text-xs text-amber-700 font-medium">
                        {healthReport.critical_count} Critical • {healthReport.warning_count} Warnings
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-extrabold text-amber-600 font-mono">
                      {healthReport.health_score}
                    </span>
                    <span className="text-xs text-slate-400">/100</span>
                  </div>
                </div>

                {/* Vulnerability Cards */}
                <div className="space-y-3">
                  {healthReport.vulnerabilities.map((vuln) => (
                    <div
                      key={vuln.id}
                      className="p-3.5 bg-white rounded-xl border border-amber-200 shadow-xs space-y-2.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          {vuln.severity}
                        </span>
                        <span className="text-xs font-mono text-slate-400">
                          {vuln.affected_nodes.join(', ')}
                        </span>
                      </div>

                      <h5 className="text-sm font-semibold text-slate-900">{vuln.title}</h5>
                      <p className="text-xs text-slate-600 leading-relaxed">{vuln.description}</p>

                      <div className="p-2 rounded bg-slate-50 border border-slate-200 text-[11px] text-slate-500">
                        <span className="font-semibold text-slate-700">Failure scenario:</span> {vuln.failure_scenario}
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <button
                          onClick={() => {
                            onApplyFix(vuln);
                            handleWriteMiroFix('Fallback Cache Guardrail');
                          }}
                          className="flex items-center justify-center space-x-1.5 py-1.5 px-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold transition-all cursor-pointer shadow-xs active:scale-95"
                        >
                          <Wrench className="w-3.5 h-3.5" />
                          <span>Apply Guardrail</span>
                        </button>

                        <button
                          onClick={() => handleWriteMiroNote(vuln.description)}
                          disabled={isWritingToMiro}
                          className="flex items-center justify-center space-x-1.5 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                          title="Write warning sticky note directly to Miro board via Miro App API"
                        >
                          <Share2 className="w-3.5 h-3.5 text-amber-600" />
                          <span>{isWritingToMiro ? 'Writing...' : 'Pin to Miro'}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 px-4 bg-amber-50/50 rounded-xl border border-dashed border-amber-200 text-amber-800 text-xs space-y-2">
                <Shield className="w-8 h-8 text-amber-500 mx-auto" />
                <p className="font-semibold">No Audit Run Yet</p>
                <p className="text-slate-500">
                  Click the <span className="font-bold text-amber-700">"Break My Agent"</span> button in the header to run an adversarial chaos audit against your agent.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Session Telemetry Footer */}
      <div className="border-t border-slate-200 px-5 py-3.5 bg-slate-50/60 flex items-center justify-between text-xs text-slate-500 shrink-0">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1">
            <Cpu className="w-4 h-4 text-slate-400" />
            <span className="font-mono font-semibold text-slate-800">
              {traces.length * 420 + 850}
            </span>
            <span>tokens</span>
          </span>
          <span className="flex items-center space-x-1">
            <Coins className="w-4 h-4 text-slate-400" />
            <span className="font-mono font-semibold text-slate-800">
              ${((traces.length * 420 + 850) * 0.0000015).toFixed(4)}
            </span>
          </span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span className="font-medium text-emerald-700">Miro App Sync Ready</span>
        </div>
      </div>
    </aside>
  );
};
