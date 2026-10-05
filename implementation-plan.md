# BoardMorph: Miro × Qwen — Visual Agent Builder
## Finalized Master Implementation Plan & Architecture Specification

**Project:** Miro × Qwen — Visual Agent Builder  
**Product Name:** BoardMorph  
**Revision:** 2.0 (Critique, Hardening & Final Specification)  
**Objective:** Deliver an end-to-end, demo-hardened system where users design multi-node AI agent workflows on a Miro canvas, Qwen interprets and compiles the visual topology into an executable graph specification, and the execution engine executes the agent live with streaming visual traces, real-time node lighting, and an automated adversarial "Break My Agent" audit.

---

## 1. Executive Summary & Critical Review

### 1.1 Original Plan Critique: Strengths, Fatal Gaps & Mitigations

The original implementation plan established a strong product narrative ("visual thinking as the programming interface") and identified a standout differentiator ("Break My Agent"). However, an engineering audit reveals several critical vulnerabilities that would lead to failure during a live build or hackathon presentation:

| Area | Original Plan Weakness / Failure Mode | Root Risk | Hardened Engineering Fix (v2.0) |
| :--- | :--- | :--- | :--- |
| **Miro Ingestion** | Assumed simple "Miro SDK/API" without defining auth flow, while stating auth is out of scope. | Miro REST API requires OAuth2/bearer tokens, CORS proxies, and registered developer apps. A live-only API breaks if tokens expire or wifi lags. | **Triple-Ingestion Architecture**: 1. Direct Miro REST API via board ID + token; 2. Miro Web SDK Canvas App (in-iframe, zero-OAuth); 3. **Failsafe Offline Preset / Paste Ingestion** with pre-baked JSON boards. |
| **Graph Extraction** | Naive extraction of "objects and connectors". Connectors in Miro often float without snapping, shapes lack explicit types, and text is unstructured. | Broken/disconnected graph with missing edges; runtime crashes before reaching LLM. | **Spatial Proximity Heuristics & Tag Parser**: Normalizes shapes, sticky notes, and cards. Fuzzy regex parses `[TYPE: tag]` or color bands. Geometric nearest-neighbor snaps loose connectors. |
| **Qwen Compilation** | Treated Qwen as an unconstrained JSON generator without schema guarantees or prompt synthesis specifications. | LLM hallucination, schema parsing failure, missing parameter bindings between nodes. | **Constrained Schema & Prompt Synthesizer**: Pydantic v2 strict models with instructor/JSON-mode. Qwen generates missing node system prompts and parameter routing. Automatic single-pass schema repair. |
| **Execution Engine** | Described as a "simple sequential executor" using unsafe string conditions (`condition: "intent == research"`). | Cannot handle fan-out/fan-in, conditional branches, or loops; Python `eval()` is a critical security vulnerability. | **Deterministic State-Machine DAG Executor**: Explicit `State` context dictionary. Deterministic branch matching on structured classification keys. No unsafe `eval()`. |
| **Trace & UX** | Static execution trace proposed as text cards without streaming. | Users stare at a frozen screen for 15-30s while LLM runs, ruining the visual demo illusion. | **SSE (Server-Sent Events) Reactive Engine**: Real-time event streaming (`node_started`, `token_stream`, `node_completed`, `edge_active`) driving glowing React Flow canvas animations. |
| **Break My Agent** | Conceptual list of problems without structured scoring, adversarial inputs, or automated diffing. | Vague feedback that cannot be demonstrated or fixed in the UI. | **Dual-Engine Chaos Auditor**: 1. Deterministic Static Graph Linter (dead ends, unreachable nodes); 2. Qwen Adversarial Stress-Tester (edge cases, failure injection, 0-100 Health Score, visual fix diffs). |
| **Timeline Feasibility** | Linear 10-minute phases where a bug in Phase 2 halts the entire demo. | High probability of zero working demo at the 2-hour mark. | **De-risked Vertical Slices**: Offline mock runtime functional in Minute 20; live API layered on top without blocking end-to-end functionality. |

---

## 2. Core Product Concept & User Journey

### 2.1 The Value Proposition
AgentForge bridges the divide between visual conceptualization and executable agent infrastructure. Instead of writing boilerplate orchestration in LangGraph, CrewAI, or AutoGen, users sketch their mental model on a whiteboard. Qwen provides the cognitive translation layer that bridges ambiguous spatial diagrams with deterministic execution semantics.

```text
┌────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│   Miro Board   │ ───► │  Qwen Semantic Compiler │ ───► │ SSE Execution & Linter  │
│ Visual Diagram │      │  Graph → Agent Contract │      │ Live Canvas Trace + Fix │
└────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### 2.2 End-to-End User Journey
1. **Design**: User arranges nodes on Miro (e.g., `[INPUT] User Query` → `[LLM] Classifier` → `[TOOL] Search` / `[TOOL] Database` → `[LLM] Synthesizer` → `[OUTPUT] Answer`).
2. **Compile**: User clicks **"Compile Agent"** in AgentForge. The system extracts shapes and connectors, builds a normalized topological graph, and feeds it to Qwen.
3. **Inspect**: Qwen fills in operational logic (prompts, tool parameters, condition rules) and displays the compiled DAG in an interactive visual canvas.
4. **Execute**: User enters a live prompt (e.g. *"Analyze EV battery adoption trends"*). The execution engine runs the workflow, streaming progress to the canvas so nodes illuminate as they process.
5. **Break My Agent**: User triggers the Chaos Auditor. Qwen stress-tests the workflow with adversarial inputs and edge cases, highlighting structural flaws (e.g., missing tool fallbacks) with a numerical Health Score (e.g., `64/100`).
6. **Visual Fix & Re-run**: User updates the Miro diagram (or clicks "Apply Recommended Fix"), recompiles, and watches the Health Score rise to `98/100`.

---

## 3. System Architecture

```text
                               ┌────────────────────────────────────────────────────────┐
                               │                      MIRO INGESTION                    │
                               │  - REST API Connector (Bearer Token + Board ID)        │
                               │  - Miro Web SDK Panel (In-board iframe)                │
                               │  - Offline Preset / JSON Import (Demo Fail-safe)       │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ Raw Board Items & Connectors
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │               BOARD PARSER & NORMALIZER                │
                               │  - Tag & Color Heuristics ([INPUT], [LLM], [TOOL], etc) │
                               │  - Spatial Proximity Connector Snapping                │
                               │  - Geometric Adjacency Matrix & Topology Clean-up      │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ Normalized Graph Topology
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │           QWEN SEMANTIC WORKFLOW COMPILER              │
                               │  - Role Deduction & Node Prompt Synthesizer             │
                               │  - Dynamic Edge Condition Binding                      │
                               │  - Input/Output Payload Mapping                        │
                               │  - Pydantic v2 Schema Validation & 1-Pass Auto-Repair  │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ Validated Executable AgentSpec
                                                           ▼
                ┌──────────────────────────────────────────┴──────────────────────────────────────────┐
                │                                                                                     │
                ▼                                                                                     ▼
┌───────────────────────────────┐                                                     ┌───────────────────────────────┐
│     AGENT RUNTIME ENGINE      │                                                     │   BREAK MY AGENT (AUDITOR)    │
│  - State Machine Context Dict │                                                     │  - Static DAG Topology Linter │
│  - Deterministic Branch Match │                                                     │  - Qwen Adversarial Generator │
│  - Sandboxed Tool Registry    │                                                     │  - Vulnerability Scoring      │
│  - SSE Streaming Event Bus    │                                                     │  - Visual Diff Recommendation │
└───────────────┬───────────────┘                                                     └───────────────┬───────────────┘
                │                                                                                     │
                │ Real-time Event Stream (SSE)                                                        │ Health Report JSON
                └──────────────────────────────────────────┬──────────────────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │                   AGENTFORGE WEB UI                    │
                               │  - Interactive Graph Canvas (React Flow / @xyflow)      │
                               │  - Real-time Node Illumination & Edge Particle Flow    │
                               │  - Live Execution Trace & Token Console                │
                               │  - Chaos Health Audit & One-Click Fix Panel            │
                               └────────────────────────────────────────────────────────┘
```

---

## 4. Formal Data Contracts & Pydantic Schemas

### 4.1 Ingestion & Parsed Graph Schema (`backend/app/models/graph.py`)

```python
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

NodeType = Literal["input", "llm", "tool", "decision", "output"]

class MiroItemRaw(BaseModel):
    id: str
    type: str  # shape, sticky_note, text, card
    content: str
    x: float
    y: float
    width: float
    height: float
    fill_color: Optional[str] = None

class MiroConnectorRaw(BaseModel):
    id: str
    start_item_id: Optional[str] = None
    end_item_id: Optional[str] = None
    label: Optional[str] = None
    start_point: Optional[Dict[str, float]] = None
    end_point: Optional[Dict[str, float]] = None

class ParsedNode(BaseModel):
    id: str
    node_type: NodeType
    title: str
    raw_text: str
    x: float
    y: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParsedEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    label: Optional[str] = None
    condition_hint: Optional[str] = None

class NormalizedGraph(BaseModel):
    nodes: List[ParsedNode]
    edges: List[ParsedEdge]
    entry_node_id: str
    exit_node_ids: List[str]
```

### 4.2 Compiled Executable Agent Specification (`backend/app/models/agent_spec.py`)

```python
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class LLMNodeConfig(BaseModel):
    system_prompt: str
    temperature: float = 0.2
    expected_output_format: Literal["text", "json"] = "text"
    json_schema: Optional[Dict[str, Any]] = None

class ToolNodeConfig(BaseModel):
    tool_name: str
    parameters_mapping: Dict[str, str] = Field(
        default_factory=dict, 
        description="Maps global state keys to tool arguments"
    )

class DecisionNodeConfig(BaseModel):
    evaluation_key: str
    routes: Dict[str, str] = Field(
        description="Key matches output value -> Target Node ID"
    )
    default_route: str

class CompiledNode(BaseModel):
    id: str
    type: Literal["input", "llm", "tool", "decision", "output"]
    label: str
    description: str
    config: Dict[str, Any]
    input_keys: List[str] = Field(default_factory=list)
    output_key: str

class CompiledEdge(BaseModel):
    id: str
    source: str
    target: str
    condition_value: Optional[str] = None

class ExecutableAgentSpec(BaseModel):
    agent_name: str
    description: str
    version: str = "1.0.0"
    nodes: List[CompiledNode]
    edges: List[CompiledEdge]
    entry_point: str
    required_state_keys: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 4.3 Runtime State & Execution Trace (`backend/app/models/execution.py`)

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class StepTrace(BaseModel):
    step_number: int
    node_id: str
    node_type: str
    node_label: str
    started_at: float
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    status: Literal["running", "completed", "failed", "skipped"]
    input_payload: Dict[str, Any]
    output_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ExecutionEvent(BaseModel):
    event_type: Literal[
        "execution_started", 
        "node_started", 
        "node_stream_chunk", 
        "node_completed", 
        "node_failed", 
        "execution_completed"
    ]
    node_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
```

### 4.4 Break My Agent Audit Models (`backend/app/models/audit.py`)

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "warning", "info"]

class Vulnerability(BaseModel):
    id: str
    severity: Severity
    category: Literal["structural", "reliability", "prompt", "security"]
    title: str
    affected_nodes: List[str]
    description: str
    failure_scenario: str
    recommended_fix: str

class RecommendedDiff(BaseModel):
    action: Literal["add_node", "remove_node", "update_edge", "replace_prompt"]
    target_node_id: Optional[str] = None
    proposed_node_type: Optional[str] = None
    proposed_label: Optional[str] = None
    details: str

class HealthReport(BaseModel):
    health_score: int = Field(ge=0, le=100)
    summary: str
    critical_count: int
    warning_count: int
    vulnerabilities: List[Vulnerability]
    recommended_diffs: List[RecommendedDiff]
    adversarial_test_cases: List[str]
```

---

## 5. Miro Ingestion & Spatial Heuristic Normalization

### 5.1 Ingestion Sources
1. **Live Miro REST API (v2)**:
   - Endpoint: `GET https://api.miro.com/v2/boards/{board_id}/items`
   - Endpoint: `GET https://api.miro.com/v2/boards/{board_id}/connectors`
   - Headers: `Authorization: Bearer {token}`
2. **Miro Web SDK (Canvas App Panel)**:
   - Client-side code runs in Miro sidebar: `await miro.board.get({ type: ['shape', 'sticky_note', 'connector'] })`
   - Directly posts payload to backend `/api/miro/parse-raw`.
3. **Preset Board Repository (Zero-Dependency Fallback)**:
   - Pre-loaded boards: `research_assistant.json`, `support_router.json`, `code_review_agent.json`.
   - Raw JSON paste textarea in the UI for instant offline testing.

### 5.2 Heuristic Normalization Engine (`miro_parser.py`)
Miro diagrams created by humans have inherent irregularities: unaligned nodes, missing tags, and loose connector endpoints. The normalizer applies five deterministic rules:

1. **Node Type Extraction**:
   - Matches regex prefix: `^\[?(INPUT|LLM|TOOL|DECISION|OUTPUT)\]?[\s:-]*(.*)$` (case-insensitive).
   - If no prefix is present, color-mapping fallback:
     - Green (`#d5f692`, `#00ff00`) → `input`
     - Light Blue (`#a6ccf5`, `#2d9cdb`) → `llm`
     - Yellow (`#fff9b1`, `#f2c94c`) → `tool`
     - Orange / Diamond shape (`#f5d192`, `#f2994a`) → `decision`
     - Purple / Red (`#e1bdf5`, `#bb6bd9`, `#eb5757`) → `output`
2. **Connector Snapping (Geometric Fallback)**:
   - If connector has missing `start_item_id` or `end_item_id`, calculate Euclidean distance from connector endpoint `(x, y)` to bounding boxes of all nodes. Snap to nearest node if distance `< 40px`.
3. **Connector Direction Normalization**:
   - Validate arrows. If bidirectional or non-directional, enforce top-to-bottom / left-to-right flow using `(y_target > y_source) or (x_target > x_source)`.
4. **Isolated Subgraph Pruning**:
   - Run DFS from `input` node. Mark unreachable nodes with warnings in `validation.warnings`.

---

## 6. Qwen Semantic Workflow Compiler

### 6.1 Compiler Responsibilities
The backend graph builder handles physical topology. Qwen handles the semantic layer:
1. Translating sparse labels (e.g. *"Check spam"*) into detailed, robust system instructions.
2. Generating structured schemas for decision nodes so they output predictable keys.
3. Mapping data flow from node outputs into downstream node inputs.
4. Auto-repairing minor structural ambiguities.

### 6.2 Compiler Prompt & Few-Shot Specification (`agent_compiler.txt`)

```text
You are the AgentForge Semantic Graph Compiler.
You receive a normalized visual workflow graph containing nodes, text descriptions, and edge connections.
Your task is to compile this visual diagram into a strictly validated, production-grade ExecutableAgentSpec JSON.

RULES:
1. PRESERVE TOPOLOGY: Do not alter the core execution path designed by the user.
2. SYNTHESIZE PROMPTS: For LLM nodes with brief labels (e.g. "Classifier"), write a comprehensive, crystal-clear system prompt specifying exact responsibilities and output constraints.
3. STRUCTURED DECISIONS: For DECISION nodes, guarantee that the preceding LLM node outputs JSON containing a routing key, and define explicit route mappings.
4. PARAMETER BINDING: Map required input arguments for TOOL nodes from state keys produced by upstream nodes.
5. STRICT JSON ONLY: Return ONLY valid JSON matching the ExecutableAgentSpec schema without markdown formatting or code blocks.
```

### 6.3 Auto-Repair Schema Middleware
If `pydantic.ValidationError` is triggered when parsing Qwen's output:
1. Capture validation error details (`e.errors()`).
2. Feed errors back to Qwen in a 1-shot repair prompt:
   `"The previous JSON was invalid for schema ExecutableAgentSpec due to: {errors}. Fix the JSON and output only the corrected JSON."`
3. If repair fails, fall back to the deterministic baseline compiler (heuristically synthesized spec).

---

## 7. Execution Runtime Engine

### 7.1 Runtime Architecture
The runtime is an asynchronous DAG state machine with an event emitter bus. It avoids unsafe Python `eval()` calls by using deterministic JSON key matching.

```text
Global State Context:
{
  "user_input": "...",
  "node_outputs": {
     "classifier": {"route": "research", "confidence": 0.95},
     "research_tool": {"results": ["EV battery density rose 12% in 2025..."]}
  },
  "current_node": "synthesizer",
  "history": [...]
}
```

### 7.2 Execution Loop & Step Mechanics

```python
async def execute_agent(spec: ExecutableAgentSpec, initial_input: str, event_bus: EventBus):
    state = {
        "user_input": initial_input,
        "node_outputs": {},
        "current_node": spec.entry_point
    }
    
    current_node_id = spec.entry_point
    visited_count = 0
    max_steps = 25  # Guard against infinite loops
    
    await event_bus.emit(ExecutionEvent(event_type="execution_started", data={"spec_name": spec.agent_name}))

    while current_node_id and visited_count < max_steps:
        visited_count += 1
        node = get_node(spec, current_node_id)
        
        await event_bus.emit(ExecutionEvent(
            event_type="node_started", 
            node_id=node.id, 
            data={"label": node.label, "type": node.type}
        ))
        
        # Execute node logic
        start_time = time.time()
        try:
            output = await dispatch_node_execution(node, state, event_bus)
            state["node_outputs"][node.id] = output
            
            await event_bus.emit(ExecutionEvent(
                event_type="node_completed", 
                node_id=node.id, 
                data={"output": output, "duration_ms": (time.time() - start_time) * 1000}
            ))
        except Exception as exc:
            await event_bus.emit(ExecutionEvent(
                event_type="node_failed", 
                node_id=node.id, 
                data={"error": str(exc)}
            ))
            raise exc

        # Advance to next node
        if node.type == "output":
            break
        elif node.type == "decision":
            eval_key = node.config["evaluation_key"]
            val = str(output.get(eval_key, node.config["default_route"]))
            current_node_id = node.config["routes"].get(val, node.config["default_route"])
        else:
            outgoing_edges = [e for e in spec.edges if e.source == node.id]
            current_node_id = outgoing_edges[0].target if outgoing_edges else None

    await event_bus.emit(ExecutionEvent(
        event_type="execution_completed", 
        data={"final_result": state["node_outputs"].get(node.id)}
    ))
```

### 7.3 Sandboxed Tool Registry
Built-in lightweight demo tools:
1. `search_tool`: DuckDuckGo Instant Answers API + live scraping fallback. Mock toggle returns rich pre-cached search payloads if network is degraded.
2. `calculator`: Safe AST-evaluated arithmetic (no `eval()`).
3. `knowledge_lookup`: In-memory vector/keyword store for documentation search.
4. `database_mock`: Structured customer/product mock data query engine.

---

## 8. "Break My Agent" Chaos Engineering Engine

The "Break My Agent" feature operates as an adversarial agent linter and security stress-tester.

```text
                     ┌────────────────────────────────┐
                     │     Compiled Agent Graph       │
                     └───────────────┬────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐
    │   STATIC GRAPH LINTER   │             │   QWEN ADVERSARIAL LLM  │
    │  - Unreachable nodes    │             │  - Edge case generator  │
    │  - Missing fallback     │             │  - Semantic ambiguity   │
    │  - Cyclic deadlocks     │             │  - Hallucination risks  │
    │  - Missing end node     │             │  - Prompt jailbreaks    │
    └────────────┬────────────┘             └────────────┬────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                     ┌────────────────────────────────┐
                     │    COMBINED HEALTH REPORT      │
                     │  - Health Score (0 - 100)      │
                     │  - Categorized Vulnerabilities │
                     │  - Visual Diff Recommendation  │
                     └────────────────────────────────┘
```

### 8.1 Static Linter Checks
1. **Unbounded Tool Invocation**: Tool nodes without timeout or conditional error branch.
2. **Dangling Decision Path**: Decision node missing a `default` or fallback route.
3. **Dead-End LLM Node**: Non-output node with 0 outgoing edges.
4. **Input Oblivion**: Workflow where `input` is not referenced in downstream prompt templates.

### 8.2 Qwen Adversarial Auditor Prompt (`break_agent_prompt.txt`)
Qwen tests the agent against 3 generated edge-case personas:
1. **The Empty/Garbage Input**: What happens if input is blank, emoji, or non-English?
2. **The Tool Failure**: What happens if the external API returns HTTP 500 or timeout?
3. **The Adversarial Injection**: What happens if input attempts prompt injection?

Qwen calculates the Health Score:
$$\text{Score} = 100 - (25 \times N_{\text{critical}}) - (10 \times N_{\text{warning}}) - (3 \times N_{\text{info}})$$
*(clamped between 0 and 100)*.

---

## 9. Frontend Architecture & Visual Experience

### 9.1 UI Layout & Component Hierarchy
Built with React, Vite, Tailwind CSS, Lucide icons, and `@xyflow/react` (React Flow).

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  AgentForge  │ Board: [Research Assistant ▼]  [Connect Miro] [⚙ Compile Agent]         │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│                                          │                                             │
│          REACT FLOW CANVAS               │               CONTROL & TRACE               │
│                                          │                                             │
│   ┌───────────────┐                      │  Tabs: [Execution Trace] [Break Report]     │
│   │ INPUT         │                      │                                             │
│   │ User Request  │                      │  Test Query:                                │
│   └───────┬───────┘                      │  ┌───────────────────────────────────────┐  │
│           │ (flowing particle)           │  │ EV battery market trends 2026         │  │
│   ┌───────▼───────┐                      │  └───────────────────────────────────────┘  │
│   │ LLM (ACTIVE)  │ ◄ glowing green ring │  [ ▶ Run Workflow ]  [ ⚡ Break My Agent ]   │
│   │ Classifier    │                      │                                             │
│   └───┬───────┬───┘                      │  Live Event Stream:                         │
│       │       │                          │  ✓ 11:45:01 [Input] Received query          │
│   ┌───▼───┐ ┌─▼─────┐                    │  ✓ 11:45:03 [Classifier] Route: research    │
│   │ TOOL  │ │ TOOL  │                    │  → 11:45:04 [Tool: Search] Executing...     │
│   └───────┘ └───────┘                    │                                             │
│                                          │                                             │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

### 9.2 Real-time Visual Execution Effects
- **Node Statuses**: `idle` (slate border), `running` (pulsing blue/green glow with spinning badge), `completed` (solid emerald border with green check), `failed` (rose border with alert icon).
- **Edge Animation**: React Flow animated strokes (`animated: true`, stroke `#10b981`) illuminate the active branch in real-time as execution traverses the graph.
- **Break Report Visual Overlay**: Vulnerable nodes highlighted with an amber/red warning shield; clicking a vulnerability highlights the offending node and renders a ghost "Recommended Fix" node on the canvas.

---

## 10. Repository File Structure

```text
miroxagent-builder/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── agent.py            # Compile, inspect, export endpoints
│   │   │   ├── audit.py            # Break My Agent chaos endpoints
│   │   │   ├── execution.py        # SSE execution runner endpoint
│   │   │   └── miro.py             # Miro REST API & raw ingestion
│   │   ├── core/
│   │   │   ├── config.py           # Settings, API keys, CORS
│   │   │   └── event_bus.py        # Async event emitter for SSE
│   │   ├── models/
│   │   │   ├── agent_spec.py       # Pydantic executable agent schema
│   │   │   ├── audit.py            # Health report & vulnerability models
│   │   │   ├── execution.py        # Trace & streaming event models
│   │   │   └── graph.py            # Miro raw & parsed graph models
│   │   ├── prompts/
│   │   │   ├── agent_compiler.py   # Qwen graph compiler prompt
│   │   │   └── break_auditor.py    # Qwen adversarial audit prompt
│   │   ├── services/
│   │   │   ├── agent_runtime.py    # DAG state-machine execution engine
│   │   │   ├── chaos_auditor.py    # Static linter + Qwen auditor
│   │   │   ├── miro_parser.py      # Spatial & tag heuristic normalizer
│   │   │   ├── qwen_compiler.py    # Qwen API integration & schema repair
│   │   │   └── tools_registry.py   # DuckDuckGo, Calculator, Mock DB
│   │   └── main.py                 # FastAPI application factory
│   ├── presets/
│   │   ├── research_assistant.json # Preset 1: Classification & Research
│   │   ├── support_router.json     # Preset 2: Support escalation workflow
│   │   └── breakable_agent.json    # Preset 3: Intentional flaws for demo
│   ├── requirements.txt
│   └── tests/
│       ├── test_parser.py
│       ├── test_compiler.py
│       └── test_runtime.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── canvas/
│   │   │   │   ├── AgentCanvas.tsx      # React Flow canvas wrapper
│   │   │   │   ├── CustomNodes.tsx      # Input, LLM, Tool, Decision nodes
│   │   │   │   └── AnimatedEdge.tsx     # Flowing pulse connector
│   │   │   ├── console/
│   │   │   │   ├── ExecutionConsole.tsx # Live SSE stream & trace logs
│   │   │   │   └── InputForm.tsx        # Query submission bar
│   │   │   ├── inspector/
│   │   │   │   ├── AgentInspector.tsx   # Compiled spec node inspector
│   │   │   │   └── BreakReportPanel.tsx # Health score & vulnerability cards
│   │   │   └── navbar/
│   │   │       └── Header.tsx           # Board switcher, compile button
│   │   ├── hooks/
│   │   │   ├── useAgentExecution.ts     # SSE connection & state manager
│   │   │   └── useMiroBoard.ts          # Miro API & preset loader
│   │   ├── services/
│   │   │   └── api.ts                   # Axios / fetch client
│   │   ├── types/
│   │   │   └── agent.ts                 # TypeScript types mirroring Pydantic
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
└── README.md
```

---

## 11. De-risked Two-Hour Build Plan

To guarantee a fully functioning, presentation-ready product within 120 minutes, development is organized into 5 de-risked vertical milestones:

```text
[ T+00m ] ─────────────────────────────────────────────────────────────┐
  │  MILESTONE 1: Core Foundation & Preset Runtime (00-30 min)         │
  │  - Backend skeleton + Pydantic models                              │
  │  - Deterministic DAG executor + mock tool registry                 │
  │  - Test end-to-end execution of pre-baked graph via CLI            │
  ├────────────────────────────────────────────────────────────────────┤
  │  MILESTONE 2: Qwen Semantic Compiler & Auto-Repair (30-55 min)     │
  │  - Qwen prompt pipeline compiling graph to ExecutableAgentSpec     │
  │  - Pydantic schema validation + 1-pass auto-repair                 │
  │  - Verify dynamic prompt synthesis for sparse nodes                │
  ├────────────────────────────────────────────────────────────────────┤
  │  MILESTONE 3: Reactive Frontend & SSE Stream (55-85 min)           │
  │  - Vite + Tailwind + React Flow canvas setup                       │
  │  - Custom styled nodes with live status illumination               │
  │  - SSE event stream lighting up nodes during live runs             │
  ├────────────────────────────────────────────────────────────────────┤
  │  MILESTONE 4: Miro Ingestion & Parser Heuristics (85-105 min)      │
  │  - Miro REST API connector + token input modal                     │
  │  - Heuristic parser (tags, colors, geometric snapping)             │
  │  - Preset fallback switcher for instant offline testing            │
  ├────────────────────────────────────────────────────────────────────┤
  │  MILESTONE 5: "Break My Agent" Chaos Auditor & Hardening (105-120m)│
  │  - Static DAG linter + Qwen adversarial audit endpoint             │
  │  - Health Score badge (0-100) & vulnerability cards in UI          │
  │  - Dry run of the Golden Path Demo Script                          │
[ T+120m ] ────────────────────────────────────────────────────────────┴─► READY TO PRESENT
```

---

## 12. Golden Path Demo Presentation Script

This script guarantees the maximum audience impact in 4 minutes:

1. **The Hook (0:00 - 0:40)**:
   - *"Every AI developer sketches agent graphs on a whiteboard before building them. But moving from that sketch into LangGraph or CrewAI code takes hours of prompt tuning and state plumbing. What if the whiteboard diagram itself was the executable application?"*
2. **The Visual Board (0:40 - 1:15)**:
   - Show a live Miro board: `[INPUT] Request` → `[LLM] Classifier` → `[TOOL] Search` → `[LLM] Synthesizer` → `[OUTPUT]`.
   - Click **"Compile Agent"** in AgentForge.
   - Show Qwen transforming the loose sticky notes into a clean, typed DAG in React Flow with synthesized system prompts.
3. **Live Execution (1:15 - 2:10)**:
   - Type query: *"What are the key technical breakthroughs in sodium-ion batteries in 2025?"*
   - Click **"Run Workflow"**.
   - Audience watches nodes pulse and turn emerald green in real-time as the Classifier routes to Search, the search tool executes, Qwen synthesizes the answer, and the final response appears in the console.
4. **The Climax: "Break My Agent" (2:10 - 3:15)**:
   - *"It works on the happy path. But is this agent production-ready? Let's find out."*
   - Click **"Break My Agent"**.
   - Qwen executes chaos stress-tests. Health Score drops to **62/100 (Critical Warning)**:
     - ⚠️ *"No fallback defined if Search tool times out or returns empty."*
     - ⚠️ *"Classifier prompt lacks confidence scoring."*
5. **The Visual Fix (3:15 - 4:00)**:
   - Jump to Miro. Add a `[TOOL] Fallback Cache` node connected to the `[LLM] Synthesizer`.
   - Click **"Re-compile"**.
   - Re-run **"Break My Agent"**: Health Score jumps to **96/100**.
   - Final line: *"AgentForge turns visual thinking directly into resilient, executable AI agents."*

---

## 13. Security, Sandboxing & Production Hardening

1. **Zero Execution of Arbitrary Code**:
   - Qwen never outputs raw Python or JavaScript. It outputs declarative JSON configurations executed by pre-defined backend handlers.
2. **Safe Expression Evaluation**:
   - Branch routing evaluates equality matches against parsed JSON fields; no `eval()` or `exec()` is permitted.
3. **Tool Execution Sandboxing**:
   - Web requests enforce strict timeouts (5 seconds max).
   - Mock data toggles automatically activate if network calls fail.
4. **API Credential Isolation**:
   - Miro tokens and Qwen keys remain exclusively in backend environment variables (`.env`) or temporary session memory. Never sent to the client bundle.
