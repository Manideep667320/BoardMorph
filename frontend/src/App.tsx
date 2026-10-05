import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/navbar/Header';
import { AgentCanvas } from './components/canvas/AgentCanvas';
import { Sidebar } from './components/sidebar/Sidebar';
import type {
  ExecutableAgentSpec,
  CompiledNode,
  StepTrace,
  HealthReport,
  Vulnerability,
} from './types/agent';
import {
  getMiroConfig,
  updateMiroConfig,
  importFromMiro,
  streamAgentExecution,
  runAgent,
  writeAuditToMiro,
  writeFixToMiro,
} from './services/api';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export const App: React.FC = () => {
  const [spec, setSpec] = useState<ExecutableAgentSpec | null>(null);

  // Miro Live Sync state
  const [activeMiroBoardId, setActiveMiroBoardId] = useState<string>('');
  const [hasMiroToken, setHasMiroToken] = useState<boolean>(false);
  const [isLiveSyncActive, setIsLiveSyncActive] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncedAt, setLastSyncedAt] = useState<Date | null>(null);
  const [toast, setToast] = useState<{
    type: 'success' | 'warning' | 'info' | 'error';
    message: string;
  } | null>(null);

  // Execution state
  const [userInput, setUserInput] = useState<string>(
    'Compare latest breakthroughs in solid-state batteries and commercial timeline'
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [traces, setTraces] = useState<StepTrace[]>([]);
  const [finalOutput, setFinalOutput] = useState<any>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Chaos Audit state
  const [healthReport, setHealthReport] = useState<HealthReport | null>(null);

  const toastTimerRef = useRef<any>(null);
  const showToast = (
    type: 'success' | 'warning' | 'info' | 'error',
    message: string,
    durationMs: number = 3500
  ) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ type, message });
    toastTimerRef.current = setTimeout(() => setToast(null), durationMs);
  };

  // 1. Initial Load: Fetch Miro Configuration
  useEffect(() => {
    async function initMiro() {
      try {
        const config = await getMiroConfig();
        if (config.board_id) {
          setActiveMiroBoardId(config.board_id);
        }
        setHasMiroToken(config.has_token);

        // If board and token exist, pull initial state
        if (config.board_id && config.has_token) {
          setIsSyncing(true);
          try {
            const initialSpec = await importFromMiro(config.board_id);
            setSpec(initialSpec);
            setLastSyncedAt(new Date());
            showToast('success', `Connected to Miro board: ${config.board_id.slice(0, 16)}...`);
          } catch (e: any) {
            console.warn('Initial Miro sync notice:', e.message);
          } finally {
            setIsSyncing(false);
          }
        }
      } catch (err) {
        console.error('Failed to load Miro configuration:', err);
      }
    }
    initMiro();
  }, []);

  // 2. Real-time Live Sync Stream via Server-Sent Events (SSE)
  useEffect(() => {
    if (!isLiveSyncActive || !activeMiroBoardId.trim()) {
      return;
    }

    const cleanBoardId = activeMiroBoardId.replace(/^https?:\/\/.*(?:board|welcomeonboard)\//, '').replace(/[/?#].*$/, '');
    const sseUrl = `/api/miro/live-stream?board_id=${encodeURIComponent(cleanBoardId)}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.addEventListener('board_synced', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload && payload.spec) {
          setSpec(payload.spec);
          setLastSyncedAt(new Date());
          showToast(
            'success',
            `⚡ Miro whiteboard updated: ${payload.items_count} items, ${payload.connectors_count} links`
          );
        }
      } catch (err) {
        console.error('Error parsing live-stream update:', err);
      }
    });

    eventSource.addEventListener('board_empty', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        setSpec(null);
        showToast('info', payload.message || 'Miro canvas is currently empty.');
      } catch {}
    });

    eventSource.addEventListener('auth_required', () => {
      setHasMiroToken(false);
      showToast('warning', 'Miro App Access Token required to sync live board data.');
    });

    eventSource.addEventListener('auth_error', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        setHasMiroToken(false);
        showToast('error', `Miro Auth Error: ${payload.error || 'Token expired or invalid'}`);
      } catch {}
    });

    eventSource.addEventListener('sync_error', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        console.warn('Live sync warning:', payload.error);
      } catch {}
    });

    eventSource.onerror = () => {
      // EventSource reconnects automatically in background
    };

    return () => {
      eventSource.close();
    };
  }, [isLiveSyncActive, activeMiroBoardId]);

  // Handle Manual "Sync Now"
  const handleSyncNow = async () => {
    if (!activeMiroBoardId.trim()) {
      showToast('warning', 'Please configure your Miro Board ID first.');
      return;
    }
    setIsSyncing(true);
    try {
      const updatedSpec = await importFromMiro(activeMiroBoardId, undefined, true);
      setSpec(updatedSpec);
      setLastSyncedAt(new Date());
      setTraces([]);
      setFinalOutput(null);
      showToast('success', 'Miro board successfully synchronized!');
    } catch (err: any) {
      showToast('error', `Sync failed: ${err.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  // Handle Miro Board & Token Updates
  const handleUpdateConfig = async (newBoardId: string, newToken?: string) => {
    const res = await updateMiroConfig(newBoardId, newToken);
    setActiveMiroBoardId(res.board_id);
    setHasMiroToken(res.has_token);
    setIsSyncing(true);
    try {
      const updatedSpec = await importFromMiro(res.board_id, newToken, true);
      setSpec(updatedSpec);
      setLastSyncedAt(new Date());
      showToast('success', 'Miro configuration saved & board synchronized!');
    } catch (err: any) {
      showToast('info', `Connected to Miro board: ${res.board_id}`);
    } finally {
      setIsSyncing(false);
    }
  };

  // Write audit note directly to Miro board
  const handleWriteAuditToMiro = async (content: string) => {
    if (!activeMiroBoardId) return;
    await writeAuditToMiro(activeMiroBoardId, content);
    showToast('success', '⚠️ Audit warning sticky note pinned directly to Miro canvas!');
  };

  // Write fix guardrail shape directly to Miro board
  const handleWriteFixToMiro = async (title: string) => {
    if (!activeMiroBoardId) return;
    await writeFixToMiro(activeMiroBoardId, title);
    showToast('success', '✅ Guardrail shape placed directly on live Miro whiteboard!');
  };

  // Run Workflow with Live SSE Streaming & Sync Fallback
  const handleRun = async () => {
    let targetSpec = spec;
    if (!targetSpec) {
      const boardToFetch = activeMiroBoardId.trim();
      if (boardToFetch) {
        showToast('info', 'Syncing agent specification from Miro whiteboard...');
        setIsSyncing(true);
        try {
          targetSpec = await importFromMiro(boardToFetch);
          setSpec(targetSpec);
          setLastSyncedAt(new Date());
        } catch (syncErr: any) {
          showToast('error', `Could not load Miro agent: ${syncErr.message}`);
          setIsSyncing(false);
          return;
        } finally {
          setIsSyncing(false);
        }
      } else {
        showToast('warning', 'Please connect your Miro board in Settings first.');
        return;
      }
    }

    if (!userInput.trim()) {
      showToast('warning', 'Please enter a test prompt or trigger query first.');
      return;
    }

    if (isRunning) return;
    setIsRunning(true);
    setTraces([]);
    setFinalOutput(null);
    setActiveNodeId(targetSpec.entry_point || null);

    try {
      await streamAgentExecution(targetSpec, userInput, (event) => {
        if (event.event_type === 'node_started') {
          setActiveNodeId(event.node_id || null);
          setTraces((prev) => {
            const stepNum = event.data?.step_number || prev.length + 1;
            const existingIdx = prev.findIndex((t) => t.node_id === event.node_id);
            const traceItem: StepTrace = {
              step_number: stepNum,
              node_id: event.node_id || '',
              node_type: event.data?.type || '',
              node_label: event.data?.label || '',
              started_at: Date.now(),
              status: 'running',
            };
            if (existingIdx >= 0) {
              const updated = [...prev];
              updated[existingIdx] = { ...updated[existingIdx], ...traceItem };
              return updated;
            }
            return [...prev, traceItem];
          });
        } else if (event.event_type === 'node_completed') {
          setTraces((prev) => {
            const existingIdx = prev.findIndex((t) => t.node_id === event.node_id);
            if (existingIdx >= 0) {
              const updated = [...prev];
              updated[existingIdx] = {
                ...updated[existingIdx],
                status: 'completed',
                completed_at: Date.now(),
                duration_ms: event.data?.duration_ms,
                output_payload: event.data?.output,
              };
              return updated;
            }
            return [
              ...prev,
              {
                step_number: event.data?.step_number || prev.length + 1,
                node_id: event.node_id || '',
                node_type: event.data?.type || '',
                node_label: event.data?.label || '',
                started_at: Date.now() - (event.data?.duration_ms || 100),
                completed_at: Date.now(),
                duration_ms: event.data?.duration_ms,
                output_payload: event.data?.output,
                status: 'completed',
              },
            ];
          });
        } else if (event.event_type === 'node_failed') {
          setTraces((prev) =>
            prev.map((t) =>
              t.node_id === event.node_id
                ? {
                    ...t,
                    status: 'failed',
                    completed_at: Date.now(),
                    error_message: event.data?.error || 'Node execution failed',
                  }
                : t
            )
          );
          setActiveNodeId(null);
        } else if (event.event_type === 'execution_completed') {
          setActiveNodeId(null);
          setFinalOutput(event.data?.final_output ?? event.data);
          showToast('success', '⚡ Agent workflow executed successfully!');
        }
      });
    } catch (err: any) {
      console.warn('SSE stream interrupted, falling back to sync runner:', err);
      try {
        showToast('info', 'Streaming unavailable, running synchronous execution...');
        const syncResult = await runAgent(targetSpec, userInput);
        setTraces(syncResult.traces || []);
        setFinalOutput(syncResult.final_output);
        if (syncResult.status === 'success') {
          showToast('success', '⚡ Agent workflow executed successfully!');
        } else {
          showToast('warning', `Agent finished with status: ${syncResult.status}`);
        }
      } catch (syncErr: any) {
        showToast('error', `Execution failed: ${syncErr.message}`);
      }
    } finally {
      setIsRunning(false);
      setActiveNodeId(null);
    }
  };

  // Break My Agent Chaos Audit
  const handleBreakAgent = () => {
    if (!spec) return;

    const vulns: Vulnerability[] = [];
    const targetIds = new Set(spec.edges.map((e) => e.target));
    const sourceIds = new Set(spec.edges.map((e) => e.source));

    // Check 1: Disconnected nodes
    spec.nodes.forEach((n) => {
      if (n.type !== 'input' && !targetIds.has(n.id)) {
        vulns.push({
          id: `vuln-${n.id}-unreachable`,
          severity: 'warning',
          category: 'structural',
          title: `Unreachable Node: [${n.label}]`,
          affected_nodes: [n.id],
          description: `Node '${n.label}' has no incoming edges and cannot be reached during execution.`,
          failure_scenario: 'Execution completes without ever executing this intended step.',
          recommended_fix: 'Connect upstream node or remove isolated component in Miro.',
        });
      }
      if (n.type !== 'output' && !sourceIds.has(n.id)) {
        vulns.push({
          id: `vuln-${n.id}-deadend`,
          severity: 'critical',
          category: 'structural',
          title: `Dead End: [${n.label}]`,
          affected_nodes: [n.id],
          description: `Node '${n.label}' has 0 outgoing connections. Execution halts prematurely.`,
          failure_scenario: 'Agent terminates without reaching final response output node.',
          recommended_fix: 'Connect outgoing path to downstream synthesizer or output node in Miro.',
        });
      }
    });

    // Check 2: Unprotected Tool node (missing fallback)
    const toolNodes = spec.nodes.filter((n) => n.type === 'tool');
    toolNodes.forEach((t) => {
      vulns.push({
        id: `vuln-${t.id}-fallback`,
        severity: 'critical',
        category: 'reliability',
        title: `Single Point of Failure on [${t.label}]`,
        affected_nodes: [t.id],
        description: `The external tool '${t.label}' has no fallback or timeout error handling. If the service experiences HTTP 500 or network lag, the workflow breaks.`,
        failure_scenario: 'Network timeout results in entire agent halt with unhandled exception.',
        recommended_fix: 'Inject a fallback cache / secondary knowledge retrieval branch.',
      });
    });

    const criticalCount = vulns.filter((v) => v.severity === 'critical').length;
    const warningCount = vulns.filter((v) => v.severity === 'warning').length;
    const healthScore = Math.max(0, 100 - criticalCount * 22 - warningCount * 10);

    setHealthReport({
      health_score: healthScore,
      summary: `Chaos audit identified ${vulns.length} vulnerabilities in current whiteboard workflow.`,
      critical_count: criticalCount,
      warning_count: warningCount,
      info_count: 0,
      vulnerabilities: vulns,
      recommended_diffs: [
        {
          action: 'add_node',
          target_node_id: toolNodes[0]?.id,
          proposed_node_type: 'tool',
          proposed_label: 'Fallback Cache Guardrail',
          details: 'Inject resilient fallback layer',
        },
      ],
      adversarial_test_cases: [
        'Tool timeout: Return HTTP 504 Gateway Timeout after 5000ms',
        'Payload injection: Attempt prompt breakout via search query',
      ],
    });
  };

  // Apply Recommended Guardrail Fix
  const handleApplyFix = (vuln: Vulnerability) => {
    if (!spec) return;

    const fallbackNodeId = `node_fallback_${Date.now().toString().slice(-4)}`;
    const updatedNodes: CompiledNode[] = [
      ...spec.nodes,
      {
        id: fallbackNodeId,
        type: 'tool' as const,
        label: 'Fallback Cache & Guardrail',
        description: 'Auto-injected resilience cache when primary retrieval times out.',
        config: {
          tool_name: 'knowledge_lookup',
          system_prompt: 'Cache retrieval for failover safety.',
        },
        input_keys: ['query'],
        output_key: 'fallback_result',
      },
    ];

    const affectedId = vuln.affected_nodes[0];
    const updatedEdges = [
      ...spec.edges,
      {
        id: `edge_fix_${Date.now().toString().slice(-4)}`,
        source: affectedId || spec.entry_point,
        target: fallbackNodeId,
        condition_value: 'on_error',
      },
    ];

    setSpec({
      ...spec,
      nodes: updatedNodes,
      edges: updatedEdges,
    });

    if (healthReport) {
      const remainingVulns = healthReport.vulnerabilities.filter((v) => v.id !== vuln.id);
      const crit = remainingVulns.filter((v) => v.severity === 'critical').length;
      const warn = remainingVulns.filter((v) => v.severity === 'warning').length;
      setHealthReport({
        ...healthReport,
        health_score: Math.min(100, Math.max(0, 100 - crit * 22 - warn * 10)),
        critical_count: crit,
        warning_count: warn,
        vulnerabilities: remainingVulns,
        summary: `Vulnerability resolved. Health score upgraded!`,
      });
    }

    // Also write back the fix shape to live Miro!
    handleWriteFixToMiro('Fallback Cache Guardrail');
  };

  const selectedNode = spec?.nodes.find((n) => n.id === selectedNodeId) || null;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans antialiased">
      {/* Real-time Header */}
      <Header
        boardId={activeMiroBoardId}
        hasToken={hasMiroToken}
        isLiveSyncActive={isLiveSyncActive}
        onToggleLiveSync={() => setIsLiveSyncActive(!isLiveSyncActive)}
        onSyncNow={handleSyncNow}
        onUpdateConfig={handleUpdateConfig}
        onRun={handleRun}
        onBreak={handleBreakAgent}
        isRunning={isRunning}
        isSyncing={isSyncing}
        vulnerabilityCount={healthReport?.vulnerabilities.length || 0}
        lastSyncedAt={lastSyncedAt}
      />

      {/* Main Studio Viewport */}
      <div className="flex flex-1 pt-16 h-[calc(100vh-64px)] overflow-hidden relative">
        {/* Canvas Engine */}
        <div className="flex-1 h-full relative">
          <AgentCanvas
            spec={spec}
            activeNodeId={activeNodeId}
            traces={traces}
            vulnerabilities={healthReport?.vulnerabilities || []}
            boardId={activeMiroBoardId}
            onOpenConfig={() => {}}
            onSelectNode={setSelectedNodeId}
          />
        </div>

        {/* Right Inspection & Telemetry Sidebar */}
        <Sidebar
          spec={spec}
          userInput={userInput}
          setUserInput={setUserInput}
          isRunning={isRunning}
          onRun={handleRun}
          traces={traces}
          finalOutput={finalOutput}
          selectedNode={selectedNode}
          healthReport={healthReport}
          onApplyFix={handleApplyFix}
          onWriteAuditToMiro={handleWriteAuditToMiro}
          onWriteFixToMiro={handleWriteFixToMiro}
        />
      </div>

      {/* Subtle Live Sync Notification Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div
            className={`flex items-center space-x-2.5 px-4 py-2.5 rounded-full shadow-lg border text-xs font-semibold backdrop-blur-md ${
              toast.type === 'success'
                ? 'bg-white/95 text-emerald-800 border-emerald-200 shadow-emerald-500/10'
                : toast.type === 'warning'
                ? 'bg-white/95 text-amber-800 border-amber-200 shadow-amber-500/10'
                : toast.type === 'error'
                ? 'bg-white/95 text-rose-800 border-rose-200 shadow-rose-500/10'
                : 'bg-white/95 text-slate-800 border-slate-200 shadow-slate-500/10'
            }`}
          >
            {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
            {toast.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-600" />}
            {toast.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-600" />}
            {toast.type === 'info' && <Info className="w-4 h-4 text-blue-600" />}
            <span>{toast.message}</span>
            <button
              onClick={() => setToast(null)}
              className="p-0.5 text-slate-400 hover:text-slate-600 rounded-full"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default App;
