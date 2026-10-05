export type NodeType = 'input' | 'llm' | 'tool' | 'decision' | 'output';

export interface CompiledNode {
  id: string;
  type: NodeType;
  label: string;
  description: string;
  config: Record<string, any>;
  input_keys: string[];
  output_key: string;
  x?: number | null;
  y?: number | null;
}

export interface CompiledEdge {
  id: string;
  source: string;
  target: string;
  condition_value?: string | null;
}

export interface ExecutableAgentSpec {
  agent_name: string;
  description: string;
  version: string;
  nodes: CompiledNode[];
  edges: CompiledEdge[];
  entry_point: string;
  required_state_keys: string[];
  metadata?: Record<string, any>;
}

export interface StepTrace {
  step_number: number;
  node_id: string;
  node_type: string;
  node_label: string;
  started_at: number;
  completed_at?: number | null;
  duration_ms?: number | null;
  status: 'running' | 'completed' | 'failed' | 'skipped';
  input_payload?: Record<string, any>;
  output_payload?: Record<string, any> | null;
  error_message?: string | null;
}

export interface ExecutionEvent {
  event_type:
    | 'execution_started'
    | 'node_started'
    | 'node_stream_chunk'
    | 'node_completed'
    | 'node_failed'
    | 'execution_completed';
  node_id?: string;
  data: Record<string, any>;
  timestamp: number;
}

export interface ExecutionRunResult {
  run_id: string;
  agent_name: string;
  status: 'success' | 'failed' | 'partial';
  traces: StepTrace[];
  final_output?: any;
  total_duration_ms: number;
  error?: string | null;
}

export interface Vulnerability {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: 'structural' | 'reliability' | 'prompt' | 'security';
  title: string;
  affected_nodes: string[];
  description: string;
  failure_scenario: string;
  recommended_fix: string;
}

export interface RecommendedDiff {
  action: 'add_node' | 'remove_node' | 'update_edge' | 'replace_prompt';
  target_node_id?: string;
  proposed_node_type?: string;
  proposed_label?: string;
  details: string;
}

export interface HealthReport {
  health_score: number;
  summary: string;
  critical_count: number;
  warning_count: number;
  info_count: number;
  vulnerabilities: Vulnerability[];
  recommended_diffs: RecommendedDiff[];
  adversarial_test_cases: string[];
}

export interface PresetSummary {
  id: string;
  name: string;
  description: string;
}
