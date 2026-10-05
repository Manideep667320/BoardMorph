import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_get_presets():
    response = client.get("/api/agent/presets")
    assert response.status_code == 200
    presets = response.json()
    assert len(presets) >= 3
    preset_ids = [p["id"] for p in presets]
    assert "research_assistant" in preset_ids
    assert "support_router" in preset_ids
    assert "breakable_agent" in preset_ids

def test_get_specific_preset():
    response = client.get("/api/agent/presets/research_assistant")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_name"] == "Autonomous Research Assistant"
    assert len(data["nodes"]) == 7

def test_execution_run_endpoint():
    # 1. Fetch preset
    preset_res = client.get("/api/agent/presets/research_assistant")
    spec = preset_res.json()

    # 2. Run agent
    run_res = client.post("/api/execution/run", json={
        "spec": spec,
        "user_input": "What is the commercial outlook for sodium-ion batteries?"
    })
    assert run_res.status_code == 200
    result = run_res.json()
    assert result["status"] == "success"
    assert len(result["traces"]) >= 5
    assert result["final_output"] is not None

def test_compile_endpoint():
    raw_graph = {
        "nodes": [
            {"id": "n1", "node_type": "input", "title": "User Query", "raw_text": "Input prompt"},
            {"id": "n2", "node_type": "llm", "title": "Synthesizer", "raw_text": "Answer query"},
            {"id": "n3", "node_type": "output", "title": "Final Output", "raw_text": "Display answer"}
        ],
        "edges": [
            {"id": "e1", "source_id": "n1", "target_id": "n2"},
            {"id": "e2", "source_id": "n2", "target_id": "n3"}
        ],
        "entry_node_id": "n1",
        "exit_node_ids": ["n3"]
    }
    compile_res = client.post("/api/agent/compile", json={"graph": raw_graph})
    assert compile_res.status_code == 200
    spec = compile_res.json()
    assert spec["entry_point"] == "n1"
    assert len(spec["nodes"]) == 3
