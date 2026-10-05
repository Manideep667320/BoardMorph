import pytest
import asyncio
from backend.app.models.graph import NormalizedGraph, ParsedNode, ParsedEdge
from backend.app.services.qwen_compiler import qwen_compiler
from backend.app.services.agent_runtime import AgentRuntime

@pytest.mark.asyncio
async def test_compile_sparse_graph_to_executable_spec():
    # Construct a raw normalized graph simulating parsed Miro sticky notes
    nodes = [
        ParsedNode(id="n_in", node_type="input", title="User Request", raw_text="Query regarding battery density"),
        ParsedNode(id="n_class", node_type="llm", title="Intent Classifier", raw_text="Classify request into research or database"),
        ParsedNode(id="n_dec", node_type="decision", title="Router", raw_text="Route gate"),
        ParsedNode(id="n_tool_search", node_type="tool", title="Web Search", raw_text="Search tool for web info"),
        ParsedNode(id="n_tool_db", node_type="tool", title="Database Mock", raw_text="Customer DB"),
        ParsedNode(id="n_synth", node_type="llm", title="Qwen Synthesizer", raw_text="Produce cohesive summary"),
        ParsedNode(id="n_out", node_type="output", title="Final Response", raw_text="Display to user")
    ]
    edges = [
        ParsedEdge(id="e1", source_id="n_in", target_id="n_class"),
        ParsedEdge(id="e2", source_id="n_class", target_id="n_dec"),
        ParsedEdge(id="e3", source_id="n_dec", target_id="n_tool_search", condition_hint="research"),
        ParsedEdge(id="e4", source_id="n_dec", target_id="n_tool_db", condition_hint="database"),
        ParsedEdge(id="e5", source_id="n_tool_search", target_id="n_synth"),
        ParsedEdge(id="e6", source_id="n_tool_db", target_id="n_synth"),
        ParsedEdge(id="e7", source_id="n_synth", target_id="n_out")
    ]
    graph = NormalizedGraph(
        nodes=nodes,
        edges=edges,
        entry_node_id="n_in",
        exit_node_ids=["n_out"]
    )

    # Compile the graph
    spec = await qwen_compiler.compile(graph)
    assert spec is not None
    assert spec.entry_point == "n_in"
    assert len(spec.nodes) == 7
    assert len(spec.edges) == 7

    # Verify synthesized node configs
    classifier_node = next(n for n in spec.nodes if n.id == "n_class")
    assert classifier_node.type == "llm"
    assert classifier_node.config.get("expected_output_format") == "json"

    search_node = next(n for n in spec.nodes if n.id == "n_tool_search")
    assert search_node.type == "tool"
    assert "search" in search_node.config.get("tool_name", "")

    decision_node = next(n for n in spec.nodes if n.id == "n_dec")
    assert decision_node.type == "decision"
    assert "research" in decision_node.config.get("routes", {})

    # Now execute the compiled spec end-to-end in AgentRuntime!
    runtime = AgentRuntime(spec)
    result = await runtime.run("Find latest sodium-ion battery market reports")
    assert result.status == "success"
    assert len(result.traces) >= 5
    
    # Verify the path traversed
    visited_ids = [t.node_id for t in result.traces]
    assert "n_in" in visited_ids
    assert "n_class" in visited_ids
    assert "n_dec" in visited_ids
    assert "n_tool_search" in visited_ids
    assert "n_synth" in visited_ids
    assert "n_out" in visited_ids
    assert result.final_output is not None

if __name__ == "__main__":
    asyncio.run(test_compile_sparse_graph_to_executable_spec())
    print("Milestone 2 compiler tests passed successfully!")
