import ast
import operator
import re
from typing import Dict, Any, Callable, Awaitable, List, Optional

# Safe math operators for AST calculator
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _eval_ast(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric literals are allowed")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            left = _eval_ast(node.left)
            right = _eval_ast(node.right)
            return _SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            operand = _eval_ast(node.operand)
            return _SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")
    else:
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

async def safe_calculator(expression: str = "", **kwargs) -> Dict[str, Any]:
    expr = str(expression or kwargs.get("expr", "")).strip()
    if not expr:
        return {"error": "Empty expression"}
    try:
        # Clean expression of potential dangerous characters
        cleaned = re.sub(r"[^0-9+\-*/().\s%^]", "", expr.replace("^", "**"))
        parsed = ast.parse(cleaned, mode='eval')
        val = _eval_ast(parsed.body)
        return {"expression": expr, "result": val}
    except Exception as e:
        return {"expression": expr, "error": f"Evaluation error: {str(e)}"}

# Pre-populated mock database
_MOCK_DATABASE = {
    "ev_batteries": [
        {"title": "Sodium-Ion Density Advances", "content": "Commercial sodium-ion cells reached 165 Wh/kg in late 2025, offering 40% lower cost than LFP."},
        {"title": "Solid-State Production Timelines", "content": "Semi-solid state batteries entering mass pilot production with 360 Wh/kg density and 12-minute 80% charge."},
        {"title": "Recycling Economics", "content": "Hydrometallurgical closed-loop recovery achieved 95% lithium extraction efficiency at industrial scale."}
    ],
    "customers": [
        {"id": "C-101", "name": "Acme Corp", "tier": "Enterprise", "status": "Active", "mrr": 4500},
        {"id": "C-102", "name": "Nova Labs", "tier": "Growth", "status": "Delinquent", "mrr": 1200},
        {"id": "C-103", "name": "Apex AI", "tier": "Enterprise", "status": "Active", "mrr": 9800}
    ]
}

async def search_tool(query: str = "", **kwargs) -> Dict[str, Any]:
    search_q = str(query or kwargs.get("q", "")).strip()
    # Check if we can match relevant domain terms
    lower_q = search_q.lower()
    
    results: List[Dict[str, str]] = []
    if any(k in lower_q for k in ["battery", "ev", "electric", "sodium", "lithium", "energy"]):
        results = [
            {"title": "2026 EV Battery Density & Cost Analysis", "snippet": "Global EV battery pack costs breached $95/kWh in early 2026, driven by sodium-ion and high-nickel cathode innovations.", "source": "cleanenergy-insights.org"},
            {"title": "Commercial Sodium-Ion Deployment", "snippet": "Entry-level urban electric vehicles now routinely ship with 160+ Wh/kg sodium-ion packs, reducing extreme weather degradation by 65%.", "source": "automotive-tech-review.com"},
            {"title": "Fast-Charging Cathode Breakthroughs", "snippet": "Silicon-carbon composite anodes have reached 4C continuous charging capability without dendrite formation.", "source": "materials-science-daily.net"}
        ]
    elif any(k in lower_q for k in ["support", "ticket", "customer", "billing"]):
        results = [
            {"title": "Customer Escalation SLA Policy", "snippet": "Enterprise tier issues must be acknowledged within 15 minutes and assigned to Tier-3 support engineers.", "source": "internal-wiki.local"},
            {"title": "Billing Dispute Resolution Matrix", "snippet": "Disputes under $500 can be auto-refunded if account has >6 months clean payment history.", "source": "billing-ops.local"}
        ]
    else:
        results = [
            {"title": f"Synthesis on '{search_q}'", "snippet": f"Found multiple authoritative technical articles analyzing key industry standards and verified operational telemetry for '{search_q}'.", "source": "global-intel-index.org"},
            {"title": f"Recent Technical Developments: {search_q}", "snippet": f"Comprehensive whitepaper detailing architectural patterns, cost factors, and benchmark results regarding {search_q}.", "source": "agent-research-net.io"}
        ]
    
    return {
        "query": search_q,
        "results_count": len(results),
        "results": results
    }

async def database_mock(query: str = "", table: str = "ev_batteries", **kwargs) -> Dict[str, Any]:
    t = table if table in _MOCK_DATABASE else "ev_batteries"
    records = _MOCK_DATABASE.get(t, [])
    q_str = str(query or kwargs.get("search", "")).lower()
    
    if q_str:
        filtered = [
            r for r in records
            if any(q_str in str(v).lower() for v in r.values())
        ]
        return {"table": t, "query": q_str, "count": len(filtered), "data": filtered or records[:2]}
    return {"table": t, "count": len(records), "data": records}

async def knowledge_lookup(topic: str = "", **kwargs) -> Dict[str, Any]:
    t = str(topic or kwargs.get("key", "")).lower()
    for category, items in _MOCK_DATABASE.items():
        for item in items:
            if any(t in str(v).lower() for v in item.values()):
                return {"found": True, "category": category, "item": item}
    return {"found": False, "topic": topic, "summary": f"No direct match found for '{topic}' in cached knowledge base."}

async def code_runner(code: str = "", expression: str = "", **kwargs) -> Dict[str, Any]:
    expr = expression or code or kwargs.get("expr", "")
    return await safe_calculator(expr)

async def api_caller(url: str = "", endpoint: str = "", query: str = "", **kwargs) -> Dict[str, Any]:
    target = url or endpoint or kwargs.get("path", "/api/v1/resource")
    return {
        "status": 200,
        "endpoint": target,
        "query": query or kwargs.get("q", ""),
        "payload": {"success": True, "message": f"Successfully queried external endpoint '{target}'"}
    }

async def notifier(channel: str = "slack", message: str = "", recipient: str = "", **kwargs) -> Dict[str, Any]:
    msg = message or kwargs.get("text", "") or "Notification triggered by agent workflow"
    dest = recipient or channel or kwargs.get("target", "alerts-channel")
    return {
        "status": "delivered",
        "channel": channel,
        "destination": dest,
        "timestamp": "2026-10-05T10:00:00Z",
        "message_preview": msg[:80]
    }

class ToolsRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {
            "search_tool": search_tool,
            "search": search_tool,
            "web_search": search_tool,
            "research": search_tool,
            "calculator": safe_calculator,
            "calc": safe_calculator,
            "math": safe_calculator,
            "database_mock": database_mock,
            "database": database_mock,
            "db": database_mock,
            "db_query": database_mock,
            "knowledge_lookup": knowledge_lookup,
            "knowledge": knowledge_lookup,
            "code_runner": code_runner,
            "python": code_runner,
            "api_caller": api_caller,
            "http_request": api_caller,
            "api": api_caller,
            "notifier": notifier,
            "slack": notifier,
            "email": notifier,
            "alert": notifier
        }

    def register(self, name: str, func: Callable[..., Awaitable[Dict[str, Any]]]):
        self._tools[name.lower()] = func

    def get_tool(self, name: str) -> Optional[Callable[..., Awaitable[Dict[str, Any]]]]:
        cleaned = name.lower().strip()
        return self._tools.get(cleaned)

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        tool_fn = self.get_tool(tool_name)
        if not tool_fn:
            for k, fn in self._tools.items():
                if k in tool_name.lower():
                    tool_fn = fn
                    break
        
        # Dynamic semantic mock for domain-specific tools envisioned on idea visuals
        if not tool_fn:
            logger_name = tool_name.replace("_", " ").title()
            return {
                "tool": tool_name,
                "status": "success",
                "simulated": True,
                "domain_action": f"Executed custom operation '{logger_name}'",
                "parameters_received": params,
                "data": {
                    "record_id": "REC-9481",
                    "status": "confirmed",
                    "result": f"Domain tool '{tool_name}' verified parameters and returned verified records."
                }
            }

        try:
            return await tool_fn(**params)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}", "tool": tool_name}

    def list_tools(self) -> List[str]:
        return sorted(list(set(self._tools.keys())))

tool_registry = ToolsRegistry()

