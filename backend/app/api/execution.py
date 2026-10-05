import asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.app.core.event_bus import EventBus
from backend.app.models.agent_spec import ExecutableAgentSpec
from backend.app.models.execution import ExecutionRunResult
from backend.app.services.agent_runtime import AgentRuntime

router = APIRouter(prefix="/execution", tags=["Execution"])

class ExecutionRequest(BaseModel):
    spec: ExecutableAgentSpec
    user_input: str

@router.post("/run", response_model=ExecutionRunResult)
async def run_agent(request: ExecutionRequest) -> ExecutionRunResult:
    try:
        runtime = AgentRuntime(request.spec)
        result = await runtime.run(request.user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@router.post("/stream")
async def stream_agent_execution(request: ExecutionRequest):
    """
    Executes the agent and streams step-by-step ExecutionEvent objects via SSE.
    """
    event_bus = EventBus()
    queue = event_bus.subscribe()
    runtime = AgentRuntime(request.spec, event_bus=event_bus)

    async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
        # Launch agent execution in background task
        exec_task = asyncio.create_task(runtime.run(request.user_input))
        try:
            while True:
                # Wait for next event or check task completion
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.event_type,
                        "data": event.model_dump_json()
                    }
                    if event.event_type in ["execution_completed", "node_failed"]:
                        # If execution completed or failed critically, exit generator
                        break
                except asyncio.TimeoutError:
                    if exec_task.done():
                        break
                    yield {
                        "event": "ping",
                        "data": "{}"
                    }
            # Ensure background task finishes cleanly
            await exec_task
        except asyncio.CancelledError:
            exec_task.cancel()
        finally:
            event_bus.unsubscribe(queue)

    return EventSourceResponse(event_generator())
