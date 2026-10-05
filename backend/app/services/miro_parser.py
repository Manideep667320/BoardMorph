import math
import re
from typing import List, Dict, Any, Optional, Tuple
from backend.app.models.graph import (
    MiroItemRaw,
    MiroConnectorRaw,
    ParsedNode,
    ParsedEdge,
    NormalizedGraph,
    NodeType,
    VisualFrame,
    CanvasIdeaContext
)

class MiroParser:
    def __init__(self):
        self.tag_regex = re.compile(r"^\[?(INPUT|LLM|TOOL|DECISION|OUTPUT)\]?[\s:-]*(.*)$", re.IGNORECASE)

    @staticmethod
    def extract_board_id(raw_id_or_url: str) -> str:
        """
        Extracts clean Miro board ID from either a raw ID string, welcome link, or browser URL.
        e.g. 'https://miro.com/app/board/uXjVO12345=/' -> 'uXjVO12345='
        e.g. 'https://miro.com/welcomeonboard/WEs0YzZ...=?share_link_id=...' -> 'WEs0YzZ...'
        """
        cleaned = raw_id_or_url.strip()
        welcome_match = re.search(r"welcomeonboard/([^/?#]+)", cleaned)
        if welcome_match:
            return welcome_match.group(1).rstrip("/")
        match = re.search(r"board/([^/?#]+)", cleaned)
        if match:
            return match.group(1).rstrip("/")
        cleaned = re.sub(r"[?#].*$", "", cleaned)
        return cleaned.rstrip("/")

    def parse_board_payload(
        self,
        raw_items: List[Dict[str, Any]],
        raw_connectors: List[Dict[str, Any]],
        board_title: Optional[str] = None
    ) -> NormalizedGraph:
        """
        Transforms raw Miro items and connectors into a normalized agent graph.
        Parses whole information visuals: extracts frames, sticky-note brainstorms,
        rules, tools, decisions, and connectors into an actionable CanvasIdeaContext.
        """
        nodes: List[ParsedNode] = []
        node_lookup: Dict[str, ParsedNode] = {}
        frames: List[VisualFrame] = []
        
        # Categorized visual context accumulators
        missions: List[str] = []
        rules: List[str] = []
        tools: List[str] = []
        decisions: List[str] = []
        inputs: List[str] = []
        outputs: List[str] = []

        # 1. First Pass: Identify Frames & Visual Sections
        for item in raw_items:
            itype = str(item.get("type", "")).lower()
            if itype in ["frame", "board_frame"]:
                f_id = str(item.get("id", ""))
                fdata = item.get("data", {}) or {}
                f_title = fdata.get("title") or item.get("title") or "Idea Frame"
                pos = item.get("position", {}) or {}
                geom = item.get("geometry", {}) or {}
                frames.append(VisualFrame(
                    id=f_id,
                    title=f_title,
                    x=float(pos.get("x", 0.0)),
                    y=float(pos.get("y", 0.0)),
                    width=float(geom.get("width", 400.0)),
                    height=float(geom.get("height", 300.0))
                ))

        # 2. Second Pass: Extract Items, Map to Frames, and Classify Semantic Role
        for item in raw_items:
            item_id = str(item.get("id", ""))
            itype = str(item.get("type", "")).lower()
            if not item_id or itype in ["frame", "board_frame"]:
                continue

            data = item.get("data", {}) or {}
            content = data.get("content") or item.get("content") or ""
            content_clean = re.sub(r"<[^>]+>", "", str(content)).strip()
            
            position = item.get("position", {}) or {}
            x = float(position.get("x", item.get("x", 0.0)))
            y = float(position.get("y", item.get("y", 0.0)))
            
            geometry = item.get("geometry", {}) or {}
            width = float(geometry.get("width", item.get("width", 120.0)))
            height = float(geometry.get("height", item.get("height", 100.0)))
            
            style = item.get("style", {}) or {}
            fill_color = style.get("fillColor") or item.get("fill_color")

            # Determine frame containment
            parent_frame_id = item.get("parent", {}).get("id") if isinstance(item.get("parent"), dict) else None
            matched_frame = None
            if parent_frame_id:
                matched_frame = next((f for f in frames if f.id == parent_frame_id), None)
            if not matched_frame and frames:
                for f in frames:
                    half_w = f.width / 2.0
                    half_h = f.height / 2.0
                    if (f.x - half_w <= x <= f.x + half_w) and (f.y - half_h <= y <= f.y + half_h):
                        matched_frame = f
                        break

            if matched_frame and item_id not in matched_frame.child_item_ids:
                matched_frame.child_item_ids.append(item_id)

            # Classify semantic role in idea canvas
            frame_title = matched_frame.title if matched_frame else ""
            node_type, title, category = self._classify_semantic_item(content_clean, fill_color, itype, frame_title)

            # Accumulate into semantic context
            if content_clean:
                line_summary = f"{title}: {content_clean}" if title and title not in content_clean else content_clean
                if category == "mission":
                    missions.append(line_summary)
                elif category == "rule":
                    rules.append(line_summary)
                elif category == "tool":
                    tools.append(line_summary)
                elif category == "decision":
                    decisions.append(line_summary)
                elif category == "input":
                    inputs.append(line_summary)
                elif category == "output":
                    outputs.append(line_summary)

            parsed_node = ParsedNode(
                id=item_id,
                node_type=node_type,
                title=title or f"{node_type.capitalize()} Node",
                raw_text=content_clean,
                x=x,
                y=y,
                metadata={
                    "width": width,
                    "height": height,
                    "fill_color": fill_color,
                    "miro_type": itype,
                    "frame_title": frame_title,
                    "semantic_category": category
                }
            )
            nodes.append(parsed_node)
            node_lookup[item_id] = parsed_node

        # 3. Parse and Snap Connectors
        edges: List[ParsedEdge] = []
        for conn in raw_connectors:
            conn_id = str(conn.get("id", f"edge-{len(edges)+1}"))
            start_item = conn.get("startItem", {}) or conn.get("start_item", {})
            end_item = conn.get("endItem", {}) or conn.get("end_item", {})
            
            start_id = start_item.get("id") or conn.get("start_item_id")
            end_id = end_item.get("id") or conn.get("end_item_id")

            # Snapping if detached
            if not start_id or start_id not in node_lookup:
                start_pt = conn.get("start_point") or conn.get("startPoint")
                if start_pt and isinstance(start_pt, dict):
                    start_id = self._find_nearest_node(start_pt.get("x", 0), start_pt.get("y", 0), nodes)

            if not end_id or end_id not in node_lookup:
                end_pt = conn.get("end_point") or conn.get("endPoint")
                if end_pt and isinstance(end_pt, dict):
                    end_id = self._find_nearest_node(end_pt.get("x", 0), end_pt.get("y", 0), nodes)

            if start_id and end_id and start_id in node_lookup and end_id in node_lookup and start_id != end_id:
                caption = conn.get("captions", [{}])[0].get("content", "") if conn.get("captions") else conn.get("label", "")
                caption_clean = re.sub(r"<[^>]+>", "", caption).strip()
                
                edges.append(ParsedEdge(
                    id=conn_id,
                    source_id=start_id,
                    target_id=end_id,
                    label=caption_clean or None,
                    condition_hint=caption_clean or None
                ))

        # 4. Topological Refinement for Nodes with Missing Labels
        target_ids = {e.target_id for e in edges}
        source_ids = {e.source_id for e in edges}
        for n in nodes:
            if not n.raw_text or n.raw_text.strip() == "":
                out_edges = [e for e in edges if e.source_id == n.id]
                in_edges = [e for e in edges if e.target_id == n.id]
                if n.id not in target_ids and out_edges:
                    n.node_type = "input"
                    n.title = "User Input Trigger"
                    n.raw_text = "Trigger input for workflow execution"
                elif n.id not in source_ids and in_edges:
                    n.node_type = "output"
                    n.title = "Final Response Output"
                    n.raw_text = "Delivers finalized synthesized result"
                elif len(out_edges) > 1:
                    n.node_type = "decision"
                    n.title = "Routing Decision"
                    labels = [e.label for e in out_edges if e.label]
                    n.raw_text = f"Route execution based on: {', '.join(labels) if labels else 'condition'}"
                else:
                    edge_labels = " ".join([e.label.lower() for e in (out_edges + in_edges) if e.label])
                    if any(w in edge_labels for w in ["db", "lookup", "record", "search", "tool", "query"]):
                        n.node_type = "tool"
                        n.title = "Database / Tool Execution"
                        n.raw_text = f"Tool operation: {edge_labels}"
                    else:
                        n.node_type = "llm"
                        n.title = "LLM Reasoning Step"
                        n.raw_text = "Performs reasoning and transformation"

        # 5. Determine Entry and Exit Nodes
        entry_node_id = ""
        exit_node_ids = []
        warnings = []

        if nodes:
            input_nodes = [n for n in nodes if n.node_type == "input"]
            if input_nodes:
                entry_node_id = input_nodes[0].id
            else:
                candidates = [n for n in nodes if n.id not in target_ids]
                entry_node_id = candidates[0].id if candidates else nodes[0].id

            output_nodes = [n for n in nodes if n.node_type == "output"]
            if output_nodes:
                exit_node_ids = [n.id for n in output_nodes]
            else:
                candidates = [n for n in nodes if n.id not in source_ids]
                exit_node_ids = candidates if candidates else [nodes[-1].id]
        else:
            warnings.append("No items found on Miro whiteboard.")

        if len(nodes) > 1 and len(edges) == 0:
            warnings.append("Freeform information visual detected (no connectors). Qwen will architect a complete agent topology.")

        # 6. Build CanvasIdeaContext & Markdown Digest
        summary_md_parts = [
            f"# Miro Information Visual Canvas: {board_title or 'Autonomous Agent Concept'}",
            f"Total Visual Items: {len(nodes)} | Frames: {len(frames)} | Connectors: {len(edges)}"
        ]
        if missions:
            summary_md_parts.append("\n### 💡 Mission & Core Idea:\n" + "\n".join(f"- {m}" for m in missions))
        if frames:
            summary_md_parts.append("\n### 🖼️ Conceptual Frames / Modules:\n" + "\n".join(f"- **{f.title}** ({len(f.child_item_ids)} elements)" for f in frames))
        if rules:
            summary_md_parts.append("\n### 📜 Guardrails, Persona & System Rules:\n" + "\n".join(f"- {r}" for r in rules))
        if tools:
            summary_md_parts.append("\n### 🛠️ Inferred Tools & Integrations:\n" + "\n".join(f"- {t}" for t in tools))
        if decisions:
            summary_md_parts.append("\n### 🔀 Decision Logic & Routing Criteria:\n" + "\n".join(f"- {d}" for d in decisions))
        if inputs:
            summary_md_parts.append("\n### 📥 Input Scenarios & Triggers:\n" + "\n".join(f"- {i}" for i in inputs))
        if outputs:
            summary_md_parts.append("\n### 📤 Expected Deliverables & Formats:\n" + "\n".join(f"- {o}" for o in outputs))

        canvas_context = CanvasIdeaContext(
            board_title=board_title or "Miro Idea Whiteboard",
            frames=frames,
            mission_and_goals=missions,
            persona_and_rules=rules,
            tools_mentioned=tools,
            decision_criteria=decisions,
            input_scenarios=inputs,
            output_deliverables=outputs,
            summary_markdown="\n".join(summary_md_parts)
        )

        return NormalizedGraph(
            nodes=nodes,
            edges=edges,
            entry_node_id=entry_node_id,
            exit_node_ids=exit_node_ids,
            warnings=warnings,
            canvas_context=canvas_context
        )

    def _classify_semantic_item(
        self,
        text: str,
        fill_color: Optional[str],
        miro_type: str,
        frame_title: str
    ) -> Tuple[NodeType, str, str]:
        """
        Classifies an item into (NodeType, Title, SemanticCategory).
        SemanticCategory: 'mission' | 'rule' | 'tool' | 'decision' | 'input' | 'output' | 'general'
        """
        first_line = text.split("\n")[0].strip() if text else ""
        lower = text.lower()
        frame_lower = frame_title.lower()

        # 1. Explicit tag match (e.g. "[LLM] Classifier" or "INPUT: Query")
        match = self.tag_regex.match(first_line)
        if match:
            tag = match.group(1).lower()
            title = match.group(2).strip() or first_line
            category = "tool" if tag == "tool" else "decision" if tag == "decision" else "input" if tag == "input" else "output" if tag == "output" else "general"
            return tag, title, category

        # 2. Check Frame Context
        if any(w in frame_lower for w in ["rule", "policy", "guardrail", "tone", "persona", "instruction"]):
            return "llm", first_line or "Guardrail Rule", "rule"
        if any(w in frame_lower for w in ["tool", "api", "database", "integration", "action"]):
            return "tool", first_line or "External Tool", "tool"
        if any(w in frame_lower for w in ["decision", "routing", "qualification", "criteria", "branch"]):
            return "decision", first_line or "Decision Gate", "decision"
        if any(w in frame_lower for w in ["input", "trigger", "inquiry", "user scenario"]):
            return "input", first_line or "Input Trigger", "input"
        if any(w in frame_lower for w in ["output", "deliverable", "response", "format"]):
            return "output", first_line or "Final Deliverable", "output"

        # 3. Content Keyword Analysis
        if any(w in lower for w in ["never", "always", "guardrail", "tone:", "persona:", "policy:", "constraint", "must not"]):
            return "llm", first_line or "Persona & Policy Rule", "rule"
        elif any(w in lower for w in ["mission:", "goal:", "idea:", "objective:", "problem statement"]):
            return "llm", first_line or "Agent Mission", "mission"
        elif any(w in lower for w in ["search", "calculator", "database", "api", "lookup", "query table", "webhook", "fetch"]):
            return "tool", first_line or "External Tool", "tool"
        elif any(w in lower for w in ["if ", "route based on", "triage", "branch", "decision gate", "qualification"]):
            return "decision", first_line or "Decision Gate", "decision"
        elif any(w in lower for w in ["user query", "user input", "inquiry", "customer ticket", "entry prompt"]):
            return "input", first_line or "User Request", "input"
        elif any(w in lower for w in ["final response", "output format", "deliverable", "markdown report", "send email"]):
            return "output", first_line or "Final Response", "output"

        # 4. Color fallback
        color = (fill_color or "").lower()
        if any(c in color for c in ["green", "#d5f692", "#00ff00", "light_green"]):
            return "input", first_line or "Input Trigger", "input"
        elif any(c in color for c in ["yellow", "#fff9b1", "#f2c94c"]):
            return "tool", first_line or "Tool Action", "tool"
        elif any(c in color for c in ["orange", "#f5d192", "#f2994a"]):
            return "decision", first_line or "Decision Gate", "decision"
        elif any(c in color for c in ["purple", "red", "#e1bdf5", "#eb5757"]):
            return "output", first_line or "Output Deliverable", "output"
        elif any(c in color for c in ["blue", "cyan", "#a6ccf5", "#2d9cdb"]):
            return "llm", first_line or "LLM Reasoner", "general"

        return "llm", first_line or "LLM Reasoning Node", "general"


    def _classify_node(self, text: str, fill_color: Optional[str], miro_type: str) -> Tuple[NodeType, str]:
        nt, title, _ = self._classify_semantic_item(text, fill_color, miro_type, "")
        return nt, title

    def _find_nearest_node(self, x: float, y: float, nodes: List[ParsedNode], max_dist: float = 60.0) -> Optional[str]:
        best_id = None
        min_dist = max_dist
        for node in nodes:
            dx = node.x - x
            dy = node.y - y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < min_dist:
                min_dist = dist
                best_id = node.id
        return best_id

miro_parser = MiroParser()
