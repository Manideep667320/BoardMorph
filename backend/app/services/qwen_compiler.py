import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional

from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.models.agent_spec import (
    ExecutableAgentSpec,
    CompiledNode,
    CompiledEdge,
    LLMNodeConfig,
    ToolNodeConfig,
    DecisionNodeConfig
)
from backend.app.models.graph import NormalizedGraph, ParsedNode
from backend.app.prompts.agent_compiler import COMPILER_SYSTEM_PROMPT, AUTO_REPAIR_PROMPT
from backend.app.services.tools_registry import tool_registry

logger = logging.getLogger("boardmorph.compiler")

class QwenCompiler:
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.base_url = settings.QWEN_BASE_URL
        self.model = settings.QWEN_MODEL

    async def compile(self, graph: NormalizedGraph) -> ExecutableAgentSpec:
        """
        Compiles a NormalizedGraph into a verified ExecutableAgentSpec.
        Attempts live Qwen compilation with 1-pass auto-repair,
        and falls back to intelligent deterministic synthesis if offline.
        """
        if self.api_key:
            try:
                spec = await asyncio.wait_for(self._compile_with_qwen(graph), timeout=20.0)
                pos_map = {n.id: (n.x, n.y) for n in graph.nodes}
                for n in spec.nodes:
                    if n.id in pos_map and n.x is None:
                        n.x, n.y = pos_map[n.id]
                return spec
            except Exception as e:
                logger.warning(f"Live Qwen compilation skipped/timed out: {e}. Falling back to deterministic synthesis.")

        return self._synthesize_heuristically(graph)

    async def _compile_with_qwen(self, graph: NormalizedGraph) -> ExecutableAgentSpec:
        import openai
        client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=20.0,
            default_headers=getattr(settings, "LLM_HEADERS", None)
        )

        canvas_summary = graph.canvas_context.summary_markdown if graph.canvas_context else ""
        graph_payload = graph.model_dump_json(indent=2)
        user_message = (
            "Architect a fully functional ExecutableAgentSpec JSON from this Miro whiteboard information visual:\n\n"
            f"{canvas_summary}\n\n"
            f"CANVAS GRAPH ELEMENTS:\n{graph_payload}"
        )

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": COMPILER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content or ""
        cleaned_json = self._extract_json_block(raw_content)

        try:
            return ExecutableAgentSpec.model_validate_json(cleaned_json)
        except ValidationError as val_err:
            logger.info("First-pass Qwen compilation triggered schema validation error. Initiating 1-pass auto-repair.")
            return await self._auto_repair(client, cleaned_json, str(val_err))

    async def _auto_repair(self, client: Any, raw_json: str, validation_errors: str) -> ExecutableAgentSpec:
        repair_message = AUTO_REPAIR_PROMPT.format(
            validation_errors=validation_errors,
            raw_json=raw_json
        )

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": COMPILER_SYSTEM_PROMPT},
                {"role": "user", "content": repair_message}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        repaired_content = response.choices[0].message.content or ""
        cleaned = self._extract_json_block(repaired_content)
        return ExecutableAgentSpec.model_validate_json(cleaned)

    def _extract_json_block(self, text: str) -> str:
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()
        return text

    def _synthesize_heuristically(self, graph: NormalizedGraph) -> ExecutableAgentSpec:
        """
        Intelligent deterministic semantic synthesizer.
        Handles both connected workflow graphs and freeform idea/brainstorm visual canvases.
        """
        ctx = graph.canvas_context
        board_name = (ctx.board_title if ctx and ctx.board_title else "Visual Idea").strip()

        # CASE 1: Freeform Idea Visual Canvas (no explicit connectors or disconnected brainstorm)
        if len(graph.edges) == 0 and len(graph.nodes) > 0:
            return self._synthesize_from_idea_canvas(graph)

        # CASE 2: Connected Graph / Flowchart
        compiled_nodes = []
        node_map = {n.id: n for n in graph.nodes}
        outgoing_edges_map: Dict[str, list] = {}
        for edge in graph.edges:
            outgoing_edges_map.setdefault(edge.source_id, []).append(edge)

        for p_node in graph.nodes:
            c_node = self._compile_single_node(p_node, outgoing_edges_map, node_map, ctx)
            compiled_nodes.append(c_node)

        compiled_edges = [
            CompiledEdge(
                id=e.id,
                source=e.source_id,
                target=e.target_id,
                condition_value=e.condition_hint or e.label
            )
            for e in graph.edges
        ]

        agent_name = f"{board_name} Agent"
        if graph.nodes:
            core_llms = [n.title for n in graph.nodes if n.node_type == "llm" and n.title != "LLM Node"]
            if core_llms:
                agent_name = f"{core_llms[0]} Agent"

        return ExecutableAgentSpec(
            agent_name=agent_name,
            description=f"Autonomous AI agent synthesized from Miro canvas '{board_name}'.",
            version="1.0.0",
            nodes=compiled_nodes,
            edges=compiled_edges,
            entry_point=graph.entry_node_id,
            required_state_keys=["user_input"],
            metadata={"compiler": "BoardMorph Visual Idea Synthesizer v2.0"}
        )

    def _synthesize_from_idea_canvas(self, graph: NormalizedGraph) -> ExecutableAgentSpec:
        """
        Architects a complete, executable 5-6 node agent pipeline from an unconnected
        information visual board containing concept notes, rules, tools, and goals.
        """
        ctx = graph.canvas_context
        board_name = ctx.board_title if ctx else "Concept Idea"
        
        # Determine anchor coordinates
        min_x = min([n.x for n in graph.nodes]) if graph.nodes else 100.0
        min_y = min([n.y for n in graph.nodes]) if graph.nodes else 200.0

        # Extract domain rules & tools
        rules_text = "\n".join(ctx.persona_and_rules) if ctx and ctx.persona_and_rules else "Operate with clarity, precision, and adherence to safety guidelines."
        tools_detected = ctx.tools_mentioned if ctx and ctx.tools_mentioned else []
        
        # Select appropriate tool name
        tool_name = "search_tool"
        for t in tools_detected:
            tl = t.lower()
            if any(k in tl for k in ["calc", "math", "discount", "price"]):
                tool_name = "calculator"
                break
            elif any(k in tl for k in ["database", "db", "customer", "account", "order"]):
                tool_name = "database_mock"
                break
            elif any(k in tl for k in ["knowledge", "wiki", "faq", "policy"]):
                tool_name = "knowledge_lookup"
                break

        n_input_id = f"node_input_{min_x:.0f}"
        n_router_id = f"node_router_{min_x:.0f}"
        n_decision_id = f"node_decision_{min_x:.0f}"
        n_tool_id = f"node_tool_{min_x:.0f}"
        n_synth_id = f"node_synth_{min_x:.0f}"
        n_output_id = f"node_output_{min_x:.0f}"

        compiled_nodes = [
            CompiledNode(
                id=n_input_id,
                type="input",
                label="User Scenario Ingestion",
                description="Receives incoming user inquiry, scenario, or payload.",
                config={},
                input_keys=["user_input"],
                output_key="user_input",
                x=min_x,
                y=min_y
            ),
            CompiledNode(
                id=n_router_id,
                type="llm",
                label="Strategy & Intent Classifier",
                description=f"Classifies query for '{board_name}' and determines required execution path.",
                config=LLMNodeConfig(
                    system_prompt=(
                        f"You are the strategic router for '{board_name}'. "
                        f"Domain Rules:\n{rules_text}\n"
                        "Analyze user input and classify route: 'tool_required' or 'direct_answer'. Output JSON with key 'route'."
                    ),
                    expected_output_format="json",
                    temperature=0.1
                ).model_dump(),
                input_keys=["user_input"],
                output_key="classification",
                x=min_x + 320,
                y=min_y
            ),
            CompiledNode(
                id=n_decision_id,
                type="decision",
                label="Triage & Policy Gate",
                description="Evaluates routing criteria and directs execution branch.",
                config=DecisionNodeConfig(
                    evaluation_key="route",
                    routes={
                        "tool_required": n_tool_id,
                        "direct_answer": n_synth_id
                    },
                    default_route=n_tool_id
                ).model_dump(),
                input_keys=["classification"],
                output_key="chosen_path",
                x=min_x + 640,
                y=min_y
            ),
            CompiledNode(
                id=n_tool_id,
                type="tool",
                label=f"Action Engine ({tool_name})",
                description=f"Executes domain data retrieval / calculation: {tool_name}",
                config=ToolNodeConfig(
                    tool_name=tool_name,
                    parameters_mapping={"query": "user_input", "expression": "user_input"}
                ).model_dump(),
                input_keys=["user_input"],
                output_key=f"{tool_name}_result",
                x=min_x + 960,
                y=min_y - 120
            ),
            CompiledNode(
                id=n_synth_id,
                type="llm",
                label="Knowledge Synthesizer & Policy Enforcer",
                description="Synthesizes finalized response embodying all guidelines, persona, and rules from the board.",
                config=LLMNodeConfig(
                    system_prompt=(
                        f"You are the synthesized AI Agent for '{board_name}'.\n"
                        f"CRITICAL POLICIES & PERSONA:\n{rules_text}\n\n"
                        "Synthesize an authoritative, helpful, and beautifully formatted deliverable for the user."
                    ),
                    expected_output_format="text",
                    temperature=0.3
                ).model_dump(),
                input_keys=["user_input"],
                output_key="synthesis",
                x=min_x + 1280,
                y=min_y
            ),
            CompiledNode(
                id=n_output_id,
                type="output",
                label="Final Response Output",
                description="Delivers the synthesized deliverable to the user.",
                config={},
                input_keys=["synthesis"],
                output_key="output",
                x=min_x + 1600,
                y=min_y
            ),
        ]

        compiled_edges = [
            CompiledEdge(id="e1", source=n_input_id, target=n_router_id),
            CompiledEdge(id="e2", source=n_router_id, target=n_decision_id),
            CompiledEdge(id="e3", source=n_decision_id, target=n_tool_id, condition_value="tool_required"),
            CompiledEdge(id="e4", source=n_decision_id, target=n_synth_id, condition_value="direct_answer"),
            CompiledEdge(id="e5", source=n_tool_id, target=n_synth_id, condition_value="results"),
            CompiledEdge(id="e6", source=n_synth_id, target=n_output_id),
        ]

        return ExecutableAgentSpec(
            agent_name=f"{board_name} Agent",
            description=f"Autonomous AI agent synthesized from Miro information visual '{board_name}'.",
            version="1.0.0",
            nodes=compiled_nodes,
            edges=compiled_edges,
            entry_point=n_input_id,
            required_state_keys=["user_input"],
            metadata={"compiler": "BoardMorph Visual Idea Synthesizer v2.0", "canvas_mode": "information_visual"}
        )


    def _compile_single_node(
        self,
        node: ParsedNode,
        outgoing_edges_map: Dict[str, list],
        node_map: Dict[str, ParsedNode],
        canvas_context: Optional[Any] = None
    ) -> CompiledNode:
        title_lower = node.title.lower()
        text_lower = node.raw_text.lower()
        config: Dict[str, Any] = {}
        output_key = f"{node.id}_out"

        if node.node_type == "input":
            output_key = "user_input"

        elif node.node_type == "output":
            output_key = "output"

        elif node.node_type == "tool":
            # Match registered tool
            tool_name = "search_tool"
            for t_name in tool_registry.list_tools():
                if t_name in title_lower or t_name in text_lower:
                    tool_name = t_name
                    break
            
            # Param mapping
            param_mapping = {"query": "user_input"}
            if "calc" in tool_name:
                param_mapping = {"expression": "user_input"}
            elif "database" in tool_name or "db" in tool_name:
                param_mapping = {"query": "user_input", "table": "customers"}

            config = ToolNodeConfig(
                tool_name=tool_name,
                parameters_mapping=param_mapping
            ).model_dump()
            output_key = f"{tool_name}_result"

        elif node.node_type == "decision":
            routes: Dict[str, str] = {}
            default_route = ""
            outgoing = outgoing_edges_map.get(node.id, [])
            for edge in outgoing:
                cond = edge.condition_hint or edge.label
                target = edge.target_id
                if cond:
                    routes[cond.lower()] = target
                if not default_route:
                    default_route = target

            config = DecisionNodeConfig(
                evaluation_key="route",
                routes=routes,
                default_route=default_route or (outgoing[0].target_id if outgoing else "")
            ).model_dump()
            output_key = "chosen_path"

        elif node.node_type == "llm":
            # Check if this LLM connects directly into a decision node or has branching
            outgoing = outgoing_edges_map.get(node.id, [])
            leads_to_decision = any(
                node_map.get(e.target_id) and node_map[e.target_id].node_type == "decision"
                for e in outgoing
            )
            has_multiple_branches = len(outgoing) > 1

            rules_addon = ""
            if canvas_context and getattr(canvas_context, "persona_and_rules", None):
                rules_addon = "\nDomain Rules & Policies:\n" + "\n".join(f"- {r}" for r in canvas_context.persona_and_rules)

            if leads_to_decision or has_multiple_branches or any(w in title_lower for w in ["classif", "router", "route", "intent"]):
                sys_prompt = (
                    f"You are the {node.title} node. Analyze the user request and classify into appropriate route. "
                    f"{rules_addon}\nOutput JSON with key 'route'."
                )
                config = LLMNodeConfig(
                    system_prompt=sys_prompt,
                    expected_output_format="json",
                    temperature=0.1
                ).model_dump()
                output_key = "classification"
            else:
                sys_prompt = (
                    f"You are the {node.title} node. Carefully process the user's input and prior tool data "
                    f"to perform: {node.raw_text or node.title}.{rules_addon}\nSynthesize a high quality response."
                )
                config = LLMNodeConfig(
                    system_prompt=sys_prompt,
                    expected_output_format="text",
                    temperature=0.3
                ).model_dump()
                output_key = "synthesis"

        return CompiledNode(
            id=node.id,
            type=node.node_type,
            label=node.title,
            description=node.raw_text or f"{node.title} node",
            config=config,
            input_keys=["user_input"],
            output_key=output_key,
            x=node.x,
            y=node.y
        )

qwen_compiler = QwenCompiler()
