import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models.agent_spec import ExecutableAgentSpec
from backend.app.models.graph import NormalizedGraph
from backend.app.services.qwen_compiler import qwen_compiler

router = APIRouter(prefix="/agent", tags=["Agent"])

PRESETS_DIR = Path(__file__).parent.parent.parent / "presets"

class CompileRequest(BaseModel):
    graph: NormalizedGraph

@router.get("/presets")
async def list_presets() -> List[Dict[str, str]]:
    presets = []
    if PRESETS_DIR.exists():
        for file in PRESETS_DIR.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    presets.append({
                        "id": file.stem,
                        "name": data.get("agent_name", file.stem),
                        "description": data.get("description", "")
                    })
            except Exception:
                continue
    return presets

@router.get("/presets/{preset_id}", response_model=ExecutableAgentSpec)
async def get_preset(preset_id: str) -> ExecutableAgentSpec:
    target_file = PRESETS_DIR / f"{preset_id}.json"
    if not target_file.exists():
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ExecutableAgentSpec.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load preset: {str(e)}")

@router.post("/compile", response_model=ExecutableAgentSpec)
async def compile_agent(request: CompileRequest) -> ExecutableAgentSpec:
    try:
        spec = await qwen_compiler.compile(request.graph)
        return spec
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Graph compilation failed: {str(e)}")
