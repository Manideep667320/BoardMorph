from typing import Optional, Dict, Any
from pathlib import Path
import re
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.models.agent_spec import ExecutableAgentSpec
from backend.app.services.miro_service import miro_sync_service
from backend.app.services.miro_parser import MiroParser

router = APIRouter(prefix="/miro", tags=["Miro"])

class MiroImportRequest(BaseModel):
    board_id: str
    access_token: Optional[str] = None
    force_recompile: bool = False

class MiroConfigRequest(BaseModel):
    board_id: Optional[str] = None
    access_token: Optional[str] = None

class MiroAuditWriteRequest(BaseModel):
    board_id: str
    content: str
    x: float = 300.0
    y: float = 100.0
    access_token: Optional[str] = None

class MiroFixWriteRequest(BaseModel):
    board_id: str
    title: str
    x: float = 400.0
    y: float = 200.0
    access_token: Optional[str] = None

@router.get("/config")
async def get_miro_config() -> Dict[str, Any]:
    """
    Returns current active board and whether a valid developer token is configured.
    """
    token = miro_sync_service._resolve_token()
    clean_id = MiroParser.extract_board_id(settings.MIRO_BOARD_ID) if settings.MIRO_BOARD_ID else ""
    return {
        "board_id": clean_id,
        "raw_board_id": settings.MIRO_BOARD_ID,
        "has_token": bool(token),
        "api_base": settings.MIRO_API_BASE_URL,
    }

@router.post("/config")
async def update_miro_config(request: MiroConfigRequest) -> Dict[str, Any]:
    """
    Updates the Miro board ID and access token dynamically and updates .env file.
    """
    env_file = Path(".env")
    env_content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""

    if request.board_id is not None:
        clean_id = MiroParser.extract_board_id(request.board_id)
        settings.MIRO_BOARD_ID = request.board_id
        if "MIRO_BOARD_ID=" in env_content:
            env_content = re.sub(r"MIRO_BOARD_ID=.*", f"MIRO_BOARD_ID={request.board_id}", env_content)
        else:
            env_content += f"\nMIRO_BOARD_ID={request.board_id}"

    if request.access_token is not None and request.access_token.strip():
        tok = request.access_token.strip()
        settings.MIRO_ACCESS_TOKEN = tok
        miro_sync_service.default_token = tok
        if "MIRO_ACCESS_TOKEN=" in env_content:
            env_content = re.sub(r"MIRO_ACCESS_TOKEN=.*", f"MIRO_ACCESS_TOKEN={tok}", env_content)
        else:
            env_content += f"\nMIRO_ACCESS_TOKEN={tok}"

    if env_file.exists():
        env_file.write_text(env_content, encoding="utf-8")

    return {
        "status": "updated",
        "board_id": MiroParser.extract_board_id(settings.MIRO_BOARD_ID),
        "has_token": bool(miro_sync_service._resolve_token()),
    }

@router.post("/import", response_model=ExecutableAgentSpec)
async def import_from_miro(request: MiroImportRequest) -> ExecutableAgentSpec:
    """
    Ingests live Miro board elements, detects structure, and compiles into an ExecutableAgentSpec via Qwen.
    """
    clean_board_id = MiroParser.extract_board_id(request.board_id)
    if not clean_board_id:
        raise HTTPException(status_code=400, detail="Invalid Miro board ID or URL provided.")

    try:
        spec, board_hash, items_cnt, conns_cnt = await miro_sync_service.sync_and_compile(
            board_id=clean_board_id,
            access_token=request.access_token,
            force_recompile=request.force_recompile
        )
        return spec
    except PermissionError as pe:
        raise HTTPException(status_code=401, detail=str(pe))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=400, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Miro board ingestion failed: {str(e)}")

@router.get("/live-stream")
async def live_stream_miro(
    board_id: str = Query(..., description="Miro Board ID or URL to watch"),
    access_token: Optional[str] = Query(None, description="Optional Miro Access Token override"),
    poll_interval: float = Query(2.5, description="Polling interval in seconds")
):
    """
    Server-Sent Events (SSE) stream for continuous real-time Miro synchronization.
    Whenever nodes or arrows change on the Miro whiteboard, an updated spec is pushed.
    """
    clean_board_id = MiroParser.extract_board_id(board_id)
    return StreamingResponse(
        miro_sync_service.watch_board_stream(
            board_id=clean_board_id,
            access_token=access_token,
            poll_interval_sec=poll_interval
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/write-audit")
async def write_audit_to_miro(request: MiroAuditWriteRequest) -> Dict[str, Any]:
    """
    Writes 'Break My Agent' feedback as a red sticky note directly onto the live Miro canvas.
    """
    clean_board_id = MiroParser.extract_board_id(request.board_id)
    try:
        result = await miro_sync_service.write_audit_sticky_note(
            board_id=clean_board_id,
            content=request.content,
            x=request.x,
            y=request.y,
            access_token=request.access_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write audit note to Miro: {str(e)}")

@router.post("/apply-fix")
async def write_fix_to_miro(request: MiroFixWriteRequest) -> Dict[str, Any]:
    """
    Writes a recommended fix guardrail shape directly onto the live Miro whiteboard.
    """
    clean_board_id = MiroParser.extract_board_id(request.board_id)
    try:
        result = await miro_sync_service.write_fix_node(
            board_id=clean_board_id,
            title=request.title,
            x=request.x,
            y=request.y,
            access_token=request.access_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply fix on Miro board: {str(e)}")
