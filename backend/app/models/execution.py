import time
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class StepTrace(BaseModel):
    step_number: int
    node_id: str
    node_type: str
    node_label: str
    started_at: float
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    status: Literal["running", "completed", "failed", "skipped"] = "running"
    input_payload: Dict[str, Any] = Field(default_factory=dict)
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
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class ExecutionRunResult(BaseModel):
    run_id: str
    agent_name: str
    status: Literal["success", "failed", "partial"]
    traces: List[StepTrace]
    final_output: Optional[Any] = None
    total_duration_ms: float = 0.0
    error: Optional[str] = None
