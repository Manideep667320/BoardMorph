import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeProps, Node } from '@xyflow/react';
import {
  MessageSquare,
  Sparkles,
  Globe,
  Database,
  Calculator,
  GitBranch,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldAlert,
} from 'lucide-react';
import type { CompiledNode, NodeType } from '../../types/agent';

export interface AgentNodeData extends Record<string, unknown> {
  node: CompiledNode;
  status?: 'idle' | 'running' | 'completed' | 'failed';
  latencyMs?: number;
  isVulnerable?: boolean;
  vulnerabilityWarning?: string;
  outputPreview?: string;
}

export type CustomAgentNode = Node<AgentNodeData, 'agentNode'>;

const getNodeIcon = (type: NodeType, label: string) => {
  const lbl = label.toLowerCase();
  switch (type) {
    case 'input':
      return <MessageSquare className="w-4 h-4 text-blue-600" />;
    case 'decision':
      return <GitBranch className="w-4 h-4 text-amber-600" />;
    case 'output':
      return <CheckCircle2 className="w-4 h-4 text-slate-700" />;
    case 'tool':
      if (lbl.includes('calc')) return <Calculator className="w-4 h-4 text-indigo-600" />;
      if (lbl.includes('db') || lbl.includes('database')) return <Database className="w-4 h-4 text-purple-600" />;
      return <Globe className="w-4 h-4 text-blue-600" />;
    case 'llm':
    default:
      return <Sparkles className="w-4 h-4 text-emerald-600" />;
  }
};

export const AgentNode = memo((props: NodeProps<CustomAgentNode>) => {
  const data = props.data;
  const node = data.node;
  const status = data.status || 'idle';
  const isRunning = status === 'running';
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  let borderClasses = 'border-slate-200 hover:border-slate-300';
  if (isRunning) {
    borderClasses = 'border-2 border-emerald-400 node-running';
  } else if (isCompleted) {
    borderClasses = 'border-emerald-300 shadow-xs';
  } else if (isFailed) {
    borderClasses = 'border-rose-400 bg-rose-50/20';
  } else if (data.isVulnerable) {
    borderClasses = 'border-amber-300 bg-amber-50/30';
  }

  return (
    <div
      className={`w-64 bg-white rounded-xl border p-4 shadow-sm transition-all relative ${borderClasses}`}
    >
      {/* Target input handle on left */}
      {node.type !== 'input' && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3 !h-3 !bg-white !border-2 !border-slate-400 !-left-1.5"
        />
      )}

      {/* Card Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-slate-100 flex items-center justify-center">
            {getNodeIcon(node.type, node.label)}
          </div>
          <span className="text-sm font-semibold text-slate-900 truncate max-w-[130px]" title={node.label}>
            {node.label}
          </span>
        </div>

        {/* Status Badge */}
        {isRunning ? (
          <span className="flex items-center text-emerald-700 text-xs bg-emerald-50 px-2 py-0.5 rounded-full font-semibold border border-emerald-200">
            <Loader2 className="w-3 h-3 mr-1 animate-spin text-emerald-600" />
            {data.latencyMs ? `${Math.round(data.latencyMs)}ms` : 'Active'}
          </span>
        ) : isCompleted ? (
          <span className="flex items-center text-emerald-700 text-xs bg-emerald-50 px-2 py-0.5 rounded-full font-medium border border-emerald-100">
            <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" /> Done
          </span>
        ) : isFailed ? (
          <span className="flex items-center text-rose-700 text-xs bg-rose-50 px-2 py-0.5 rounded-full font-medium border border-rose-200">
            <AlertCircle className="w-3 h-3 mr-1 text-rose-600" /> Error
          </span>
        ) : (
          <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full font-medium">
            {node.type.toUpperCase()}
          </span>
        )}
      </div>

      {/* Card Body */}
      <div className="pt-2.5 space-y-1.5 text-xs">
        <p className="text-slate-500 line-clamp-2 leading-relaxed">
          {node.description || `Handles ${node.type} processing logic.`}
        </p>

        {node.type === 'llm' && (
          <div className="flex items-center justify-between text-slate-400 pt-1">
            <span>Format:</span>
            <span className="font-mono text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">
              {node.config.expected_output_format || 'text'}
            </span>
          </div>
        )}

        {node.type === 'tool' && (
          <div className="flex items-center justify-between text-slate-400 pt-1">
            <span>Tool:</span>
            <span className="font-mono text-blue-600 font-medium bg-blue-50 px-1.5 py-0.5 rounded text-[11px]">
              {node.config.tool_name || node.label}
            </span>
          </div>
        )}

        {data.outputPreview && (
          <div className="p-2 rounded bg-slate-50 border border-slate-200 mt-2">
            <span className="text-[11px] text-slate-500 block truncate font-mono">
              {data.outputPreview}
            </span>
          </div>
        )}

        {data.isVulnerable && (
          <div className="flex items-center space-x-1 text-amber-700 bg-amber-50 p-1.5 rounded border border-amber-200 mt-1">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span className="text-[11px] font-medium truncate">
              {data.vulnerabilityWarning || 'Vulnerability detected'}
            </span>
          </div>
        )}
      </div>

      {/* Source output handle on right */}
      {node.type !== 'output' && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-white !-right-1.5"
        />
      )}
    </div>
  );
});
