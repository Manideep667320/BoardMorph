import React, { useMemo, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from '@xyflow/react';
import type { Node, Edge, NodeTypes, EdgeTypes } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Sparkles, Copy, Check, ExternalLink, Radio } from 'lucide-react';

import type { ExecutableAgentSpec, StepTrace, Vulnerability } from '../../types/agent';
import { AgentNode } from './AgentNode';
import type { AgentNodeData } from './AgentNode';
import { AnimatedFlowEdge } from './AnimatedFlowEdge';

interface AgentCanvasProps {
  spec: ExecutableAgentSpec | null;
  activeNodeId: string | null;
  traces: StepTrace[];
  vulnerabilities: Vulnerability[];
  boardId?: string;
  onOpenConfig?: () => void;
  onSelectNode?: (nodeId: string) => void;
}

const nodeTypes: NodeTypes = {
  agentNode: AgentNode as any,
};

const edgeTypes: EdgeTypes = {
  animatedFlowEdge: AnimatedFlowEdge as any,
};

const IDEA_TEMPLATES = [
  {
    id: 'support',
    title: 'Customer Support & Refund Bot',
    icon: '💬',
    prompt: `Create an Information Visual Canvas for an Autonomous Customer Support Agent:
- Frame "Agent Mission & Persona": Goal is autonomous billing and refund triage. Friendly, empathetic tone.
- Frame "Guardrails & Policies": Sticky note "Never reveal private API keys". Sticky note "Refunds permitted only if account active < 30 days".
- Frame "Tools & APIs": Tool "database_mock" for customer accounts, Tool "safe_calculator" for prorated refunds.
- Frame "Decision Gate": Route to database if account inquiry, route to calculator if refund requested, direct answer otherwise.
- Frame "Output Delivery": Clean markdown resolution summary.`
  },
  {
    id: 'intel',
    title: 'Deep-Tech Market Intelligence',
    icon: '🔬',
    prompt: `Create an Information Visual Canvas for a Market Intelligence Agent:
- Frame "Research Mission": Ingest queries on breakthroughs in clean energy & solid-state batteries.
- Frame "Knowledge Retrieval Tools": Tool "search_tool" for industry whitepapers, Tool "knowledge_lookup" for verified specs.
- Frame "Evaluation Policies": Fact-check all citations, compare cost per kWh against benchmarks.
- Frame "Executive Output": Synthesize findings into structured executive brief with source URLs.`
  },
  {
    id: 'devops',
    title: 'DevOps Incident Triage & Alerting',
    icon: '⚡',
    prompt: `Create an Information Visual Canvas for an Automated DevOps Incident Agent:
- Frame "Alert Trigger": Receives incoming PagerDuty or system telemetry payload.
- Frame "Severity Decision Gate": Classifies incident severity into P1 (Critical Outage) vs P2 (Latency Spike).
- Frame "Diagnostic Tools": Tool "database_mock" for service logs, Tool "notifier" for Slack #eng-alerts.
- Frame "Remediation Policies": If P1, notify lead engineer immediately. Synthesize root cause summary.`
  },
  {
    id: 'flowchart',
    title: 'Direct Agent Flowchart',
    icon: '🔀',
    prompt: `Create a horizontal workflow flowchart on Miro using connected cards:
1. [INPUT] User Ticket & Query Ingestion
2. [DECISION] Intent Classifier (branches: "search_required", "db_lookup", "direct_answer")
3. [TOOL] Web Research Engine (tool: search_tool)
4. [TOOL] Customer Database Query (tool: database_mock)
5. [LLM] Response Synthesizer & Fact Checker
6. [OUTPUT] Final Formatted Delivery`
  }
];

export const AgentCanvas: React.FC<AgentCanvasProps> = ({
  spec,
  activeNodeId,
  traces,
  vulnerabilities,
  boardId,
  onOpenConfig,
  onSelectNode,
}) => {
  const [selectedTemplateIndex, setSelectedTemplateIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  const activeTemplate = IDEA_TEMPLATES[selectedTemplateIndex];

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(activeTemplate.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cleanBoardId = boardId ? boardId.replace(/^https?:\/\/.*(?:board|welcomeonboard)\//, '').replace(/[/?#].*$/, '') : '';
  const miroBoardUrl = cleanBoardId ? `https://miro.com/app/board/${cleanBoardId}/` : 'https://miro.com';

  // Convert spec.nodes to ReactFlow nodes with layout
  const nodes = useMemo<Node<AgentNodeData>[]>(() => {
    if (!spec || !spec.nodes || spec.nodes.length === 0) return [];

    const traceMap = new Map<string, StepTrace>();
    traces.forEach((t) => traceMap.set(t.node_id, t));

    const vulnMap = new Map<string, string>();
    vulnerabilities.forEach((v) => {
      v.affected_nodes.forEach((nid) => vulnMap.set(nid, v.title));
    });

    // Check if Miro coordinates exist
    const validCoords = spec.nodes.filter(
      (n) => typeof n.x === 'number' && typeof n.y === 'number'
    );
    const minX = validCoords.length > 0 ? Math.min(...validCoords.map((n) => n.x as number)) : 0;
    const minY = validCoords.length > 0 ? Math.min(...validCoords.map((n) => n.y as number)) : 0;

    return spec.nodes.map((node, index) => {
      const trace = traceMap.get(node.id);
      const isRunning = activeNodeId === node.id;
      let status: 'idle' | 'running' | 'completed' | 'failed' = 'idle';

      if (isRunning) {
        status = 'running';
      } else if (trace) {
        if (trace.status === 'completed') status = 'completed';
        else if (trace.status === 'failed') status = 'failed';
        else if (trace.status === 'running') status = 'running';
      }

      // Output preview string if completed
      let outputPreview: string | undefined = undefined;
      if (trace && trace.output_payload) {
        const out = trace.output_payload;
        if (typeof out === 'string') {
          outputPreview = (out as string).slice(0, 45) + '...';
        } else if (typeof out === 'object' && out !== null) {
          const keys = Object.keys(out);
          if (keys.length > 0) {
            outputPreview = `${keys[0]}: ${String((out as Record<string, any>)[keys[0]]).slice(0, 35)}...`;
          }
        }
      }

      // Layout positioning: prefer Miro canvas coordinates directly, fallback to topological layout
      let xPos = 80 + index * 320;
      let yPos = 240;

      if (typeof node.x === 'number' && typeof node.y === 'number') {
        xPos = 80 + (node.x - minX);
        yPos = 80 + (node.y - minY);
      } else if (node.type === 'tool' && index % 2 === 0) {
        yPos = 360;
      } else if (node.type === 'tool') {
        yPos = 140;
      }

      return {
        id: node.id,
        type: 'agentNode',
        position: { x: xPos, y: yPos },
        data: {
          node,
          status,
          latencyMs: trace?.duration_ms || undefined,
          isVulnerable: vulnMap.has(node.id),
          vulnerabilityWarning: vulnMap.get(node.id),
          outputPreview,
        },
      };
    });
  }, [spec, activeNodeId, traces, vulnerabilities]);

  // Convert spec.edges to ReactFlow edges with active particle animation
  const edges = useMemo<Edge[]>(() => {
    if (!spec || !spec.edges) return [];

    const completedNodes = new Set(
      traces.filter((t) => t.status === 'completed').map((t) => t.node_id)
    );

    return spec.edges.map((edge) => {
      const isSourceCompleted = completedNodes.has(edge.source);
      const isTargetActive = activeNodeId === edge.target;
      const isTransmitting = isSourceCompleted && (isTargetActive || completedNodes.has(edge.target));

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: 'animatedFlowEdge',
        data: {
          isActive: isTransmitting,
          label: edge.condition_value || undefined,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isTransmitting ? '#10B981' : '#94A3B8',
          width: 14,
          height: 14,
        },
      };
    });
  }, [spec, activeNodeId, traces]);

  const hasNodes = nodes.length > 0;

  return (
    <div className="w-full h-full relative canvas-dots bg-[#F8FAFC]">
      {/* Floating Canvas Intelligence Banner */}
      {hasNodes && (
        <div className="absolute top-4 left-4 z-20 flex items-center space-x-2.5 bg-white/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-200/80 shadow-xs pointer-events-auto">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-bold text-slate-800 tracking-tight">
            {spec?.agent_name || 'Autonomous Agent'}
          </span>
          <span className="text-[11px] text-slate-400">|</span>
          <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
            {spec?.metadata?.canvas_mode === 'information_visual' ? '💡 Miro Visual Idea Canvas' : '🔀 Miro Whiteboard Graph'}
          </span>
          <span className="text-[11px] font-mono text-slate-500">
            {spec?.nodes.length} Nodes • {spec?.edges.length} Links
          </span>
        </div>
      )}

      {hasNodes ? (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          onNodeClick={(_, node) => onSelectNode && onSelectNode(node.id)}
          minZoom={0.2}
          maxZoom={1.5}
        >
          <Background gap={24} size={1.2} color="#CBD5E1" />
          <Controls
            className="!bg-white !border !border-slate-200 !rounded-xl !shadow-xs !p-1"
            showInteractive={false}
          />
          <MiniMap
            className="!bg-white/90 !backdrop-blur-sm !border !border-slate-200 !rounded-xl !shadow-xs !bottom-6 !right-6"
            nodeColor={(node) => {
              const data = node.data as unknown as AgentNodeData;
              if (data?.status === 'running') return '#10B981';
              if (data?.status === 'completed') return '#34D399';
              if (data?.isVulnerable) return '#F59E0B';
              return '#CBD5E1';
            }}
            maskColor="rgba(248, 250, 252, 0.7)"
          />
        </ReactFlow>
      ) : (
        /* Empty / Waiting for Miro Live Sync State */
        <div className="w-full h-full flex items-center justify-center p-6">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200 shadow-xl max-w-2xl w-full p-8 text-center space-y-6">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-blue-500/10 via-emerald-500/10 to-teal-500/10 border border-blue-200/50 flex items-center justify-center text-blue-600">
              <Radio className="w-8 h-8 text-blue-600 animate-pulse" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-slate-900">
                Connected to Miro Live Canvas
              </h2>
              <p className="text-sm text-slate-500 max-w-lg mx-auto leading-relaxed">
                In Miro, create <strong className="text-slate-700">whole information visuals for any idea</strong> — frames, sticky-note brainstorms, rules, tone of voice, tools, and decision criteria. Qwen analyzes your entire visual whiteboard and synthesizes it into a fully working, executable AI agent!
              </p>
            </div>

            {/* Idea Concept Templates Switcher */}
            <div className="space-y-3 text-left">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  <span>Choose Visual Idea Concept to Try:</span>
                </span>
                <button
                  onClick={handleCopyPrompt}
                  className="flex items-center space-x-1 text-xs font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-md transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Visual Prompt</span>
                    </>
                  )}
                </button>
              </div>

              {/* Template Tabs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 p-1 bg-slate-100 rounded-lg">
                {IDEA_TEMPLATES.map((tmpl, idx) => (
                  <button
                    key={tmpl.id}
                    onClick={() => setSelectedTemplateIndex(idx)}
                    className={`text-left px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                      selectedTemplateIndex === idx
                        ? 'bg-white text-blue-700 shadow-xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
                    }`}
                  >
                    <span className="mr-1">{tmpl.icon}</span>
                    <span className="truncate">{tmpl.title.split(' ')[0]}</span>
                  </button>
                ))}
              </div>

              {/* Prompt Preview */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600">
                  <span>{activeTemplate.title}</span>
                  <span className="text-slate-400 font-normal">Miro AI / Manual Paste</span>
                </div>
                <pre className="text-xs font-mono text-slate-700 bg-white border border-slate-200 p-3 rounded-lg max-h-36 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {activeTemplate.prompt}
                </pre>
                <p className="text-[11px] text-slate-400">
                  Paste into Miro's "Create with AI" prompt bar, or draw notes freely across frames. BoardMorph detects changes and live-compiles via Qwen in real-time.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-center space-x-3 pt-2">
              {onOpenConfig && (
                <button
                  onClick={onOpenConfig}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                >
                  Configure Board & Token
                </button>
              )}
              {cleanBoardId && (
                <a
                  href={miroBoardUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
                >
                  <span>Open Miro Whiteboard</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
