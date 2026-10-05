import asyncio
import json
from pathlib import Path
import pytest

from backend.app.core.event_bus import EventBus
from backend.app.models.agent_spec import ExecutableAgentSpec
from backend.app.services.agent_runtime import AgentRuntime
from backend.app.services.tools_registry import safe_calculator, search_tool, database_mock

@pytest.mark.asyncio
async def test_tools_execution():
    # Calculator tests
    res_calc = await safe_calculator("45 * 2 + 10")
    assert res_calc["result"] == 100
    
    res_calc_pow = await safe_calculator("2 ^ 8")
    assert res_calc_pow["result"] == 256

    # Search tool test
    res_search = await search_tool("EV battery breakthroughs 2026")
    assert res_search["results_count"] > 0
    assert "battery" in res_search["results"][0]["snippet"].lower() or "density" in res_search["results"][0]["snippet"].lower()

    # DB tool test
    res_db = await database_mock(table="customers", query="Acme")
    assert res_db["count"] >= 1
    assert res_db["data"][0]["name"] == "Acme Corp"

@pytest.mark.asyncio
async def test_runtime_research_path():
    preset_path = Path(__file__).parent.parent / "presets" / "research_assistant.json"
    with open(preset_path, "r", encoding="utf-8") as f:
        spec_dict = json.load(f)
    
    spec = ExecutableAgentSpec.model_validate(spec_dict)
    assert spec.agent_name == "Autonomous Research Assistant"
    assert len(spec.nodes) == 7

    event_bus = EventBus()
    queue = event_bus.subscribe()
    runtime = AgentRuntime(spec, event_bus=event_bus)

    # Execute research query
    result = await runtime.run("What are the key technical breakthroughs in sodium-ion EV batteries?")
    assert result.status == "success"
    assert len(result.traces) >= 5
    
    # Check that search node was executed
    node_ids_executed = [t.node_id for t in result.traces]
    assert "node_input" in node_ids_executed
    assert "node_classifier" in node_ids_executed
    assert "node_decision" in node_ids_executed
    assert "node_search" in node_ids_executed
    assert "node_synthesizer" in node_ids_executed
    assert "node_output" in node_ids_executed
    assert "node_database" not in node_ids_executed

    # Verify event emission
    events = []
    while not queue.empty():
        events.append(await queue.get())
    
    event_types = [e.event_type for e in events]
    assert "execution_started" in event_types
    assert "node_started" in event_types
    assert "node_completed" in event_types
    assert "execution_completed" in event_types

@pytest.mark.asyncio
async def test_runtime_database_path():
    preset_path = Path(__file__).parent.parent / "presets" / "research_assistant.json"
    with open(preset_path, "r", encoding="utf-8") as f:
        spec_dict = json.load(f)
    
    spec = ExecutableAgentSpec.model_validate(spec_dict)
    runtime = AgentRuntime(spec)

    # Execute database query
    result = await runtime.run("Look up customer database account records for Acme Corp")
    assert result.status == "success"
    
    node_ids_executed = [t.node_id for t in result.traces]
    assert "node_database" in node_ids_executed
    assert "node_search" not in node_ids_executed

if __name__ == "__main__":
    asyncio.run(test_tools_execution())
    asyncio.run(test_runtime_research_path())
    asyncio.run(test_runtime_database_path())
    print("All Milestone 1 runtime tests passed successfully!")
