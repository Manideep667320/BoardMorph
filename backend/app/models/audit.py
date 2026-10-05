from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "warning", "info"]

class Vulnerability(BaseModel):
    id: str
    severity: Severity
    category: Literal["structural", "reliability", "prompt", "security"]
    title: str
    affected_nodes: List[str]
    description: str
    failure_scenario: str
    recommended_fix: str

class RecommendedDiff(BaseModel):
    action: Literal["add_node", "remove_node", "update_edge", "replace_prompt"]
    target_node_id: Optional[str] = None
    proposed_node_type: Optional[str] = None
    proposed_label: Optional[str] = None
    details: str

class HealthReport(BaseModel):
    health_score: int = Field(ge=0, le=100)
    summary: str
    critical_count: int
    warning_count: int
    info_count: int = 0
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    recommended_diffs: List[RecommendedDiff] = Field(default_factory=list)
    adversarial_test_cases: List[str] = Field(default_factory=list)
