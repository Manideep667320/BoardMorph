from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

NodeType = Literal["input", "llm", "tool", "decision", "output"]

class LLMNodeConfig(BaseModel):
    system_prompt: str = "You are a helpful assistant."
    user_prompt_template: str = "{input}"
    temperature: float = 0.2
    expected_output_format: Literal["text", "json"] = "text"
    json_schema: Optional[Dict[str, Any]] = None

class ToolNodeConfig(BaseModel):
    tool_name: str
    parameters_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps global state keys to tool arguments, e.g. {'query': 'user_input'}"
    )
    fallback_value: Optional[Any] = None

class DecisionNodeConfig(BaseModel):
    evaluation_key: str = "route"
    routes: Dict[str, str] = Field(
        default_factory=dict,
        description="Value -> Target Node ID mapping"
    )
    default_route: str

class CompiledNode(BaseModel):
    id: str
    type: NodeType
    label: str
    description: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    input_keys: List[str] = Field(default_factory=list)
    output_key: str = "output"
    x: Optional[float] = None
    y: Optional[float] = None

class CompiledEdge(BaseModel):
    id: str
    source: str
    target: str
    condition_value: Optional[str] = None

class ExecutableAgentSpec(BaseModel):
    agent_name: str
    description: str = ""
    version: str = "1.0.0"
    nodes: List[CompiledNode]
    edges: List[CompiledEdge]
    entry_point: str
    required_state_keys: List[str] = Field(default_factory=lambda: ["user_input"])
    metadata: Dict[str, Any] = Field(default_factory=dict)
