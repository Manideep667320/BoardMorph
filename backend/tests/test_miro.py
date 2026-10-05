import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.miro_parser import miro_parser, MiroParser
from backend.app.services.miro_service import miro_sync_service

client = TestClient(app)

def test_miro_parser_heuristic_and_snapping():
    raw_items = [
        {"id": "item1", "type": "sticky_note", "data": {"content": "[INPUT] User Inquiry"}, "position": {"x": 50, "y": 100}},
        {"id": "item2", "type": "shape", "data": {"content": "[LLM] Classifier Node"}, "position": {"x": 300, "y": 100}},
        {"id": "item3", "type": "shape", "data": {"content": "[OUTPUT] Display Result"}, "position": {"x": 600, "y": 100}}
    ]
    # Loose connector where startPoint is near item1 (x: 55, y: 105) and endPoint is near item2 (x: 295, y: 98)
    raw_connectors = [
        {"id": "conn1", "startPoint": {"x": 55, "y": 105}, "endPoint": {"x": 295, "y": 98}},
        {"id": "conn2", "startItem": {"id": "item2"}, "endItem": {"id": "item3"}}
    ]

    graph = miro_parser.parse_board_payload(raw_items, raw_connectors)
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.entry_node_id == "item1"
    assert "item3" in graph.exit_node_ids
    
    # Check that detached connector snapped to item1 -> item2
    snapped_edge = next(e for e in graph.edges if e.id == "conn1")
    assert snapped_edge.source_id == "item1"
    assert snapped_edge.target_id == "item2"

def test_extract_board_id_all_formats():
    # 1. Full board URL with query params
    url1 = "https://miro.com/app/board/uXjVO12345=/?share_link_id=987654"
    assert MiroParser.extract_board_id(url1) == "uXjVO12345="

    # 2. Welcome onboard share link
    url2 = "https://miro.com/welcomeonboard/WEs0YzZMU1RjdnNsUjBSMmZobkVxV0NMRjJIWmFSanhuV1ZvTWRlbU1OMzRxMmJ1UVlOOENkWTJ3V1BONEE2SEg3ZEdHUm1zajdFNXhuOStJZThGRVo3OWZzUkxvTVA2QnNwcWJhejZ6SHBDWjlURGVUU1M1cklVcnVHdXA5NGZyVmtkMG5hNDA3dVlncnBvRVB2ZXBnPT0hdjE=?share_link_id=719816065731"
    assert "WEs0YzZMU1RjdnNs" in MiroParser.extract_board_id(url2)

    # 3. Raw Board ID token
    raw_id = "uXjVNi8-q48="
    assert MiroParser.extract_board_id(raw_id) == "uXjVNi8-q48="

def test_board_hash_change_detection():
    items_v1 = [
        {"id": "node1", "type": "sticky_note", "data": {"content": "Search step"}, "position": {"x": 100, "y": 200}}
    ]
    conns = []

    hash1 = miro_sync_service.compute_board_hash(items_v1, conns)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hex

    # Identical state returns identical hash
    hash1_repeat = miro_sync_service.compute_board_hash(items_v1, conns)
    assert hash1 == hash1_repeat

    # Changed content returns different hash
    items_v2 = [
        {"id": "node1", "type": "sticky_note", "data": {"content": "Updated search query"}, "position": {"x": 100, "y": 200}}
    ]
    hash2 = miro_sync_service.compute_board_hash(items_v2, conns)
    assert hash1 != hash2

    # Changed position returns different hash
    items_v3 = [
        {"id": "node1", "type": "sticky_note", "data": {"content": "Search step"}, "position": {"x": 350, "y": 200}}
    ]
    hash3 = miro_sync_service.compute_board_hash(items_v3, conns)
    assert hash1 != hash3

def test_api_miro_config():
    response = client.get("/api/miro/config")
    assert response.status_code == 200
    data = response.json()
    assert "board_id" in data
    assert "has_token" in data
    assert "api_base" in data

def test_api_miro_import_validation():
    # Attempting to import without a token should fail cleanly with 400 (not mock data!)
    response = client.post("/api/miro/import", json={
        "board_id": "test_board_without_token",
        "access_token": ""
    })
    # Since default_token in .env is "your_miro_access_token_here", it correctly rejects it
    assert response.status_code in [400, 401]

@pytest.mark.asyncio
async def test_information_visual_idea_compilation_and_execution():
    from backend.app.services.qwen_compiler import qwen_compiler
    from backend.app.services.agent_runtime import AgentRuntime

    # Simulate a user's freeform idea whiteboard (frames, rules, tools, decisions - ZERO connectors)
    raw_items = [
        {
            "id": "frame_1",
            "type": "frame",
            "data": {"title": "Customer Support Strategy"},
            "position": {"x": 200, "y": 200},
            "geometry": {"width": 800, "height": 600}
        },
        {
            "id": "note_mission",
            "type": "sticky_note",
            "data": {"content": "Goal: Autonomous customer refund and account management agent"},
            "position": {"x": 150, "y": 150}
        },
        {
            "id": "note_rule",
            "type": "sticky_note",
            "data": {"content": "Rule: Always be empathetic and polite. Never reveal private API keys."},
            "position": {"x": 300, "y": 150}
        },
        {
            "id": "note_tool",
            "type": "sticky_note",
            "data": {"content": "Tool: Database query for customer account records"},
            "position": {"x": 450, "y": 150}
        },
        {
            "id": "note_decision",
            "type": "sticky_note",
            "data": {"content": "Decision: If customer asks for account data, route to database_mock"},
            "position": {"x": 600, "y": 150}
        },
        {
            "id": "note_output",
            "type": "sticky_note",
            "data": {"content": "Output: Deliver professional markdown summary"},
            "position": {"x": 750, "y": 150}
        }
    ]
    raw_connectors = []  # No explicit connectors drawn by user!

    # 1. Parse board payload
    graph = miro_parser.parse_board_payload(raw_items, raw_connectors, board_title="Customer Copilot")
    assert graph.canvas_context is not None
    assert len(graph.canvas_context.frames) == 1
    assert len(graph.canvas_context.persona_and_rules) >= 1
    assert len(graph.canvas_context.tools_mentioned) >= 1

    # 2. Compile into ExecutableAgentSpec via Qwen compiler
    spec = await qwen_compiler.compile(graph)
    assert spec is not None
    assert len(spec.nodes) >= 5
    assert len(spec.edges) >= 4
    assert spec.entry_point != ""
    assert "Customer Copilot" in spec.agent_name

    # 3. Verify real step-by-step execution in AgentRuntime
    runtime = AgentRuntime(spec)
    result = await runtime.run("Can you look up customer records for Acme Corp?")
    assert result.status == "success"
    assert len(result.traces) >= 4
    assert result.final_output is not None

