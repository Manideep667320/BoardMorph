from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

NodeType = Literal["input", "llm", "tool", "decision", "output"]

class MiroItemRaw(BaseModel):
    id: str
    type: str  # shape, sticky_note, text, card
    content: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
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
    raw_text: str = ""
    x: float = 0.0
    y: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParsedEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    label: Optional[str] = None
    condition_hint: Optional[str] = None

class VisualFrame(BaseModel):
    id: str
    title: str
    x: float = 0.0
    y: float = 0.0
    width: float = 400.0
    height: float = 300.0
    child_item_ids: List[str] = Field(default_factory=list)

class CanvasIdeaContext(BaseModel):
    board_title: str = "Miro Idea Board"
    frames: List[VisualFrame] = Field(default_factory=list)
    mission_and_goals: List[str] = Field(default_factory=list)
    persona_and_rules: List[str] = Field(default_factory=list)
    tools_mentioned: List[str] = Field(default_factory=list)
    decision_criteria: List[str] = Field(default_factory=list)
    input_scenarios: List[str] = Field(default_factory=list)
    output_deliverables: List[str] = Field(default_factory=list)
    summary_markdown: str = ""

class NormalizedGraph(BaseModel):
    nodes: List[ParsedNode]
    edges: List[ParsedEdge]
    entry_node_id: str
    exit_node_ids: List[str]
    warnings: List[str] = Field(default_factory=list)
    canvas_context: Optional[CanvasIdeaContext] = None

