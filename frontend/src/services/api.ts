import type {
  ExecutableAgentSpec,
  ExecutionEvent,
  ExecutionRunResult,
} from '../types/agent';

export interface MiroConfig {
  board_id: string;
  raw_board_id?: string;
  has_token: boolean;
  api_base: string;
}

export interface MiroLiveSyncPayload {
  event_type: 'board_synced';
  board_id: string;
  board_title?: string;
  board_hash: string;
  items_count: number;
  connectors_count: number;
  spec: ExecutableAgentSpec;
}

export async function getMiroConfig(): Promise<MiroConfig> {
  const res = await fetch('/api/miro/config');
  if (!res.ok) throw new Error('Failed to retrieve Miro configuration');
  return res.json();
}

export async function updateMiroConfig(
  boardId?: string,
  accessToken?: string
): Promise<{ status: string; board_id: string; has_token: boolean }> {
  const res = await fetch('/api/miro/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ board_id: boardId, access_token: accessToken }),
  });
  if (!res.ok) throw new Error('Failed to update Miro configuration');
  return res.json();
}

export async function compileGraph(graph: any): Promise<ExecutableAgentSpec> {
  const res = await fetch('/api/agent/compile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ graph }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Compilation failed' }));
    throw new Error(err.detail || 'Compilation failed');
  }
  return res.json();
}

export async function importFromMiro(
  boardId: string,
  accessToken?: string,
  forceRecompile: boolean = false
): Promise<ExecutableAgentSpec> {
  const res = await fetch('/api/miro/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      board_id: boardId,
      access_token: accessToken || null,
      force_recompile: forceRecompile,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Miro sync failed' }));
    throw new Error(err.detail || 'Miro sync failed');
  }
  return res.json();
}

export async function writeAuditToMiro(
  boardId: string,
  content: string,
  accessToken?: string
): Promise<any> {
  const res = await fetch('/api/miro/write-audit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ board_id: boardId, content, access_token: accessToken || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to write audit to Miro' }));
    throw new Error(err.detail || 'Failed to write audit to Miro');
  }
  return res.json();
}

export async function writeFixToMiro(
  boardId: string,
  title: string,
  accessToken?: string
): Promise<any> {
  const res = await fetch('/api/miro/apply-fix', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ board_id: boardId, title, access_token: accessToken || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to apply fix on Miro' }));
    throw new Error(err.detail || 'Failed to apply fix on Miro');
  }
  return res.json();
}

export async function runAgent(
  spec: ExecutableAgentSpec,
  userInput: string
): Promise<ExecutionRunResult> {
  const res = await fetch('/api/execution/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ spec, user_input: userInput }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Execution failed' }));
    throw new Error(err.detail || 'Execution failed');
  }
  return res.json();
}

export async function streamAgentExecution(
  spec: ExecutableAgentSpec,
  userInput: string,
  onEvent: (event: ExecutionEvent) => void
): Promise<void> {
  const response = await fetch('/api/execution/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ spec, user_input: userInput }),
  });

  if (!response.ok || !response.body) {
    const errText = await response.text().catch(() => '');
    throw new Error(`Failed to initiate SSE execution stream: ${errText || response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let currentEvent = '';
  let dataLines: string[] = [];
  let eventCount = 0;

  const dispatchCurrent = () => {
    if (dataLines.length === 0) {
      currentEvent = '';
      return;
    }
    const rawData = dataLines.join('\n').trim();
    const eventName = currentEvent;
    currentEvent = '';
    dataLines = [];

    if (!rawData || eventName === 'ping') return;

    try {
      const parsed = JSON.parse(rawData);
      eventCount++;
      if (parsed && typeof parsed === 'object' && parsed.event_type) {
        onEvent(parsed as ExecutionEvent);
      } else {
        onEvent({
          event_type: (eventName || 'node_completed') as any,
          data: parsed,
          timestamp: Date.now() / 1000,
        });
      }
    } catch (err) {
      console.warn('Skipping unparseable SSE line:', rawData, err);
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      // Normalize CRLF and CR to LF
      buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed === '') {
          dispatchCurrent();
        } else if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          dataLines.push(line.slice(5).trim());
        }
      }
    }

    if (buffer.trim()) {
      if (buffer.startsWith('data:')) {
        dataLines.push(buffer.slice(5).trim());
      }
    }
    dispatchCurrent();
  } catch (err) {
    throw err;
  }

  if (eventCount === 0) {
    throw new Error('SSE stream completed without receiving any execution events');
  }
}

