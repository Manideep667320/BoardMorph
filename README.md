# 🎨 BoardMorph — Miro × Qwen Visual Agent Builder

> **Transform visual idea whiteboards, diagrams, and sketches in Miro into fully executable, testable, and streaming autonomous AI agents powered by Qwen.**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6+-646CFF?logo=vite)](https://vitejs.dev)
[![React Flow](https://img.shields.io/badge/React%20Flow-12+-FF4081?logo=react)](https://reactflow.dev)
[![Qwen](https://img.shields.io/badge/Model-Qwen%202.5%2072B-purple)](https://openrouter.ai/models/qwen/qwen-2.5-72b-instruct)
[![Miro](https://img.shields.io/badge/Miro-REST%20API%20v2-FFD02F?logo=miro)](https://developers.miro.com)

---

## 🌟 What is BoardMorph?

Traditional AI agent development requires writing hundreds of lines of boilerplate code in frameworks like LangGraph, CrewAI, or AutoGen. However, system architects and product designers naturally **brainstorm and sketch on whiteboards**.

**BoardMorph** bridges the divide between visual conceptualization and executable multi-agent execution:
1. **Design Naturally on Miro**: Lay out entire conceptual boards—frames grouping functional domains, sticky notes defining safety guardrails and personas, tool boxes, decision gates, or connected flowcharts.
2. **Compile via Qwen**: The Qwen 2.5 72B cognitive compiler analyzes the spatial layout, text notes, and connections, synthesizing a production-grade, executable Directed Acyclic Graph (DAG).
3. **Live Streaming Execution**: Run workflows against real user queries. Observe real-time step execution with animated flow particles, per-node latency logging, and final deliverable generation.
4. **"Break My Agent" Chaos Engineering**: Automatically audit the visual agent for structural vulnerabilities (single points of failure, missing fallbacks, dead-ends) and write red warning sticky notes **directly back onto your live Miro canvas**.

---

## 🚀 Key Features

### 💡 1. Whole Visual Idea Compilation (Beyond Simple Flowcharts)
Users don't just build rigid linear graphs. BoardMorph supports:
- **Domain Frames**: Group nodes by purpose (*"Research Mission"*, *"Customer Support Policies"*, *"Escalation Gate"*).
- **Sticky Note Policies**: Rules like *"Never reveal private customer API keys"* or *"Verify citation dates"* are extracted and embedded directly into the agent's prompts.
- **Hybrid Visual Brainstorms**: If connectors are missing, Qwen automatically architects an optimal 5–6 step autonomous pipeline (*Input &rarr; Intent Classifier &rarr; Decision Gate &rarr; Tool Invocation &rarr; LLM Synthesizer &rarr; Final Delivery*).

### ⚡ 2. Real-Time Bidirectional Miro Whiteboard Sync
- **Sub-3s Change Detection**: SHA-256 canvas fingerprinting detects whiteboard edits in Miro.
- **Server-Sent Events (SSE)**: Automatically recompiles and updates your local React Flow canvas whenever you add, delete, or move items on Miro.
- **Whiteboard Write-Back**: Pin audit warnings or guardrail shapes directly onto your live Miro whiteboard with one click.

### 🌊 3. Live Streaming Agent Runtime
- **Step-by-Step SSE Telemetry**: Real-time event streaming (`node_started`, `node_completed`, `execution_completed`).
- **Interactive Visual Canvas**: The active node glows in real time, and connectors pulse with animated particle physics as data flows from node to node.
- **Live Tool Registry**: Built-in mock tools for web search, customer database lookups, safe mathematical computation, and notification dispatch.
- **Dual Mode Execution**: Real-time SSE streaming with automatic synchronous execution fallback for rock-solid reliability.

### 🛡️ 4. "Break My Agent" Adversarial Audit
- Scans compiled graphs for structural anti-patterns:
  - 🚨 **Single Point of Failure**: Critical tools or routers with zero redundant fallback pathways.
  - ⚠️ **Dead-End Nodes**: Processing branches that never deliver a response to the user.
  - 🔄 **Orphaned / Unconnected Gates**: Decision routes lacking destination targets.
- Displays a visual **Health Score (0–100)** with actionable remediation advice.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       MIRO WHITEBOARD                       │
│  [Frames]  [Sticky Notes]  [Cards]  [Shapes]  [Connectors]  │
└──────────────────────────────┬──────────────────────────────┘
                               │  REST API v2 (Polling & Webhooks)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    BOARDMORPH BACKEND (FastAPI)              │
│                                                             │
│  1. MiroSyncService     ──> SHA-256 Fingerprint & Diffing   │
│  2. MiroParser          ──> Spatial Grouping & Normalization│
│  3. QwenCompiler        ──> Qwen 2.5 72B (OpenRouter / API) │
│  4. AgentRuntime        ──> Async Multi-Node Execution      │
│  5. EventBus            ──> SSE Event Streaming (/stream)  │
│  6. ToolRegistry        ──> Search, Database, Calculator    │
└──────────────────────────────┬──────────────────────────────┘
                               │  JSON over REST + SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   BOARDMORPH FRONTEND (React 19)            │
│                                                             │
│  • React Flow Canvas with Animated Particle Edges           │
│  • Live Step Checklist with Latency (ms) & Payload Previews │
│  • Node Inspector & Configuration Panel                     │
│  • "Break My Agent" Audit Scorecard & Miro Write-Back       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

- **Python**: `3.11` or `3.12`
- **Node.js**: `v18.0.0` or higher (Node 20+ recommended)
- **Miro Account**: Free or paid account at [miro.com](https://miro.com)
- **OpenRouter API Key**: For Qwen 2.5 72B (`sk-or-v1-...`) or DashScope key

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/boardmorph.git
cd boardmorph
```

### 2. Configure Environment Variables
Copy or edit the `.env` file in the root directory:

```ini
# ==============================================================================
# 1. Qwen / LLM Configuration via OpenRouter
# ==============================================================================
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
QWEN_BASE_URL=https://openrouter.ai/api/v1
QWEN_MODEL=qwen/qwen-2.5-72b-instruct

# ==============================================================================
# 2. Miro App Configuration (Direct REST API v2)
# ==============================================================================
# Generate your token at: https://developers.miro.com/
MIRO_ACCESS_TOKEN=eyJtaXJv...
MIRO_CLIENT_ID=your_client_id
MIRO_CLIENT_SECRET=your_client_secret
MIRO_BOARD_ID=https://miro.com/app/board/uXjVEekclY0=/
MIRO_API_BASE_URL=https://api.miro.com/v2

# ==============================================================================
# 3. Application Settings
# ==============================================================================
APP_NAME=BoardMorph
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173", "*"]
```

---

## 🔑 How to Get Your Miro Credentials

1. Go to the [Miro Developer Portal](https://developers.miro.com/) and click **"Create new app"**.
2. Select **"Expire user authorization token"** or use a persistent access token.
3. Under **Permissions / Scopes**, enable:
   - `boards:read` (Required to fetch shapes, sticky notes, frames, and connectors)
   - `boards:write` (Required for "Break My Agent" to write audit notes onto your whiteboard)
4. Go to **"Install app and get OAuth token"**, select your team, and copy the generated **Access Token**.
5. Copy your board's full link from your browser URL bar (e.g., `https://miro.com/app/board/uXjVEekclY0=/`).

---

## 🏃 Running the Application

### 1. Start the Backend Server (FastAPI)
```bash
# In the root directory:
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger UI): **`http://127.0.0.1:8000/docs`**
- Health Endpoint: **`http://127.0.0.1:8000/api/health`**

### 2. Start the Frontend Development Server (Vite)
```bash
# In another terminal:
cd frontend
npm install
npm run dev
```
- Open your browser at **`http://localhost:5173/`**

---

## 🧪 Testing

Run backend tests using `pytest`:
```bash
python -m pytest backend/tests/test_miro.py -v
```

Validate frontend production build and TypeScript types:
```bash
cd frontend
npm run build
```

---

## 📂 Project Structure

```text
boardmorph/
├── .env                                # Environment configurations (LLM & Miro)
├── implementation-plan.md              # Architectural specification & engineering design
├── README.md                           # Project documentation
│
├── backend/                            # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & middleware
│   │   ├── api/                        # REST API routers
│   │   │   ├── agent.py                # Agent compilation endpoints
│   │   │   ├── execution.py            # Synchronous & SSE streaming execution endpoints
│   │   │   └── miro.py                 # Miro config, import, live sync, and write-back
│   │   ├── core/                       # Core infrastructure
│   │   │   ├── config.py               # Pydantic BaseSettings & env resolution
│   │   │   └── event_bus.py            # Async Pub/Sub queue for SSE streaming
│   │   ├── models/                     # Pydantic v2 schemas
│   │   │   ├── agent_spec.py           # ExecutableAgentSpec, CompiledNode, CompiledEdge
│   │   │   ├── execution.py            # StepTrace, ExecutionRunResult, ExecutionEvent
│   │   │   └── graph.py                # NormalizedGraph, ParsedNode, ParsedEdge
│   │   ├── prompts/                    # Qwen cognitive compiler prompts
│   │   │   └── agent_compiler.py       # Visual-to-Agent DAG meta-prompt & repair instructions
│   │   └── services/                   # Business logic & runtime engines
│   │       ├── agent_runtime.py        # Asynchronous multi-step agent execution engine
│   │       ├── miro_parser.py          # Spatial clustering, frame association, connector resolution
│   │       ├── miro_service.py         # Miro REST API v2 client & live SSE change detection
│   │       ├── qwen_compiler.py        # Qwen 2.5 72B compiler with 1-pass auto-repair
│   │       └── tools_registry.py       # Extensible registry for search, DB, calculator tools
│   ├── presets/                        # Pre-packaged agent specifications
│   │   ├── breakable_agent.json        # Benchmark agent with intentional flaws for chaos testing
│   │   ├── research_assistant.json     # Multi-step market research pipeline
│   │   └── support_router.json         # Customer triage & refund automation pipeline
│   └── tests/                          # Pytest test suite
│       └── test_miro.py                # Unit tests for Miro parser, compiler, and endpoints
│
└── frontend/                           # React 19 + TypeScript + Vite Frontend
    ├── index.html                      # HTML root
    ├── package.json                    # Dependencies & scripts
    ├── vite.config.ts                  # Vite config with backend proxy (/api)
    └── src/
        ├── App.tsx                     # Main application layout, state & orchestration
        ├── index.css                   # Global styles & canvas animations
        ├── components/
        │   ├── canvas/                 # React Flow interactive graph canvas
        │   │   ├── AgentCanvas.tsx     # Canvas container, minimap, controls & visual idea prompts
        │   │   ├── AgentNode.tsx       # Custom node with latency, status indicators & pill tags
        │   │   └── AnimatedFlowEdge.tsx# Glowing SVG particle edge for active data transmission
        │   ├── navbar/
        │   │   └── Header.tsx          # Brand header, Miro sync toggle, Break & Run triggers
        │   └── sidebar/
        │       └── Sidebar.tsx         # Live trace checklist, Node inspector & Break audit report
        ├── services/
        │   └── api.ts                  # API client with robust SSE stream parser & sync runner
        └── types/
            └── agent.ts                # TypeScript interfaces matching backend Pydantic models
```

---

## 💡 How to Use BoardMorph

### Scenario A: Testing with an Empty or New Miro Board
1. Open BoardMorph at `http://localhost:5173/`.
2. If your Miro whiteboard is empty, BoardMorph displays four **Idea Templates** on the canvas:
   - 💬 *Customer Support & Refund Bot*
   - 🔬 *Deep-Tech Market Intelligence Agent*
   - ⚡ *DevOps Incident Triage & Alerting*
   - 🔀 *Direct Agent Flowchart*
3. Click **"Copy Idea Prompt"** on any template.
4. On Miro, open the prompt bar (or paste into notes) to generate the shapes and sticky notes.
5. BoardMorph automatically detects the new items within seconds and compiles them into a live agent on your screen!

### Scenario B: Executing the Agent
1. In the right sidebar, enter your query in the **"Test Prompt / Trigger Query"** box (e.g., *"Compare latest breakthroughs in solid-state batteries and commercial timeline"*).
2. Click **"Run Test Step"** or **"Run Workflow"**.
3. Watch the graph light up:
   - Active nodes glow green.
   - Animated green particles travel across connectors.
   - Each step's output payload and latency (in milliseconds) appear in the **Live Workflow Trace**.
   - The final formatted deliverable displays at the bottom.

### Scenario C: Running Chaos Audits ("Break My Agent")
1. Click the orange **"Break My Agent"** button in the top navigation bar.
2. The agent graph is evaluated for structural risks (missing fallbacks, disconnected decision paths).
3. The sidebar displays your **Health Score** and specific vulnerability cards.
4. Click **"Write to Miro Whiteboard"** next to any vulnerability to pin a red warning sticky note directly onto the live Miro canvas for your team to review!

---

## 🛠️ API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and LLM/Miro configuration check |
| `GET` | `/api/miro/config` | Retrieves current active Miro board ID and connection state |
| `POST` | `/api/miro/config` | Dynamically updates active board ID or access token |
| `POST` | `/api/miro/import` | Fetches whiteboard elements and compiles them via Qwen |
| `GET` | `/api/miro/live-stream` | SSE endpoint streaming real-time whiteboard updates |
| `POST` | `/api/miro/write-audit` | Writes an audit warning sticky note onto the Miro canvas |
| `POST` | `/api/miro/apply-fix` | Appends a guardrail visual shape to the Miro whiteboard |
| `POST` | `/api/agent/compile` | Compiles any normalized graph into an `ExecutableAgentSpec` |
| `POST` | `/api/execution/run` | Executes the compiled agent synchronously and returns traces |
| `POST` | `/api/execution/stream` | Streams step-by-step agent execution events via SSE |

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 🤝 Acknowledgements

- **[Miro](https://miro.com)** for their intuitive visual whiteboard platform and Developer REST APIs.
- **[Qwen Team & Alibaba Cloud](https://github.com/QwenLM)** for the Qwen 2.5 series of foundation models.
- **[OpenRouter](https://openrouter.ai)** for unified LLM inference routing.
- **[xyflow](https://reactflow.dev)** for the React Flow graph visualization library.
