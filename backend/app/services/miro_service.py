import asyncio
import hashlib
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
import httpx

from backend.app.core.config import settings
from backend.app.models.graph import NormalizedGraph
from backend.app.models.agent_spec import ExecutableAgentSpec
from backend.app.services.miro_parser import miro_parser, MiroParser
from backend.app.services.qwen_compiler import qwen_compiler

logger = logging.getLogger("boardmorph.miro_sync")

class MiroSyncService:
    """
    High-performance real-time Miro synchronization engine.
    Fetches real Miro whiteboard elements and connectors directly via Miro REST API v2,
    provides live change detection via SHA-256 fingerprinting,
    and streams board updates via Server-Sent Events (SSE).
    """

    def __init__(self, default_token: Optional[str] = None):
        self.default_token = default_token or settings.MIRO_ACCESS_TOKEN or os.getenv("MIRO_ACCESS_TOKEN", "")
        self.api_base = settings.MIRO_API_BASE_URL.rstrip("/")
        # In-memory cache for compiled specs keyed by board hash
        self._compiled_cache: Dict[str, ExecutableAgentSpec] = {}

    def _resolve_token(self, token: Optional[str] = None) -> str:
        if token is not None:
            tok = token.strip()
        else:
            tok = (self.default_token or settings.MIRO_ACCESS_TOKEN or os.getenv("MIRO_ACCESS_TOKEN", "")).strip()
        if not tok or tok.lower().startswith("your_") or "token_here" in tok.lower():
            return ""
        return tok

    def _resolve_board_id(self, board_id_or_url: str) -> str:
        clean = MiroParser.extract_board_id(board_id_or_url)
        if len(clean) > 40 and "welcomeonboard" in board_id_or_url:
            try:
                with httpx.Client(follow_redirects=True, timeout=4.0) as client:
                    res = client.get(board_id_or_url)
                    match = re.search(r"board/([^/?#]+)", str(res.url))
                    if match:
                        return match.group(1).rstrip("/")
            except Exception:
                pass
        return clean

    def compute_board_hash(self, raw_items: List[Dict[str, Any]], raw_connectors: List[Dict[str, Any]]) -> str:
        """
        Computes a deterministic SHA-256 checksum of the board elements and topology.
        Any movement, text edit, addition, or removal alters this hash.
        """
        fingerprints: List[str] = []
        
        for item in sorted(raw_items, key=lambda x: str(x.get("id", ""))):
            i_id = item.get("id", "")
            i_type = item.get("type", "")
            data = item.get("data", {}) or {}
            content = data.get("content") or item.get("content", "")
            pos = item.get("position", {}) or {}
            x = round(float(pos.get("x", item.get("x", 0.0))), 1)
            y = round(float(pos.get("y", item.get("y", 0.0))), 1)
            fingerprints.append(f"item:{i_id}:{i_type}:{content}:{x}:{y}")

        for conn in sorted(raw_connectors, key=lambda x: str(x.get("id", ""))):
            c_id = conn.get("id", "")
            start = (conn.get("startItem", {}) or conn.get("start_item", {})).get("id") or conn.get("start_item_id", "")
            end = (conn.get("endItem", {}) or conn.get("end_item", {})).get("id") or conn.get("end_item_id", "")
            captions = conn.get("captions", [])
            cap_text = captions[0].get("content", "") if captions and isinstance(captions, list) else ""
            fingerprints.append(f"conn:{c_id}:{start}->{end}:{cap_text}")

        combined = "|".join(fingerprints)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    async def fetch_board_raw(
        self,
        board_id: str,
        access_token: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Fetches live items and connectors from Miro REST API with automatic cursor pagination.
        """
        token = self._resolve_token(access_token)
        if not token:
            raise ValueError(
                "Miro Access Token is not configured. Please provide your Miro App Token in settings or .env to sync live boards."
            )

        clean_id = self._resolve_board_id(board_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Fetch Board Info
            board_info = None
            try:
                board_res = await client.get(f"{self.api_base}/boards/{clean_id}", headers=headers)
                if board_res.status_code == 200:
                    board_info = board_res.json()
                elif board_res.status_code == 401:
                    raise PermissionError("Invalid or expired Miro Access Token. Please check your developer app token.")
                elif board_res.status_code == 404:
                    raise FileNotFoundError(f"Miro board '{clean_id}' was not found. Verify the Board ID or URL.")
            except (PermissionError, FileNotFoundError):
                raise
            except Exception as e:
                logger.warning(f"Could not retrieve board metadata: {e}")

            # 2. Fetch Board Items (Sticky notes, shapes, text, cards)
            items: List[Dict[str, Any]] = []
            cursor: Optional[str] = None
            page = 0
            while page < 5:  # Max 250 items for rapid responsiveness
                params = {"limit": 50}
                if cursor:
                    params["cursor"] = cursor
                items_res = await client.get(
                    f"{self.api_base}/boards/{clean_id}/items",
                    headers=headers,
                    params=params
                )
                if items_res.status_code != 200:
                    err_msg = items_res.text
                    try:
                        err_json = items_res.json()
                        err_msg = err_json.get("message", err_msg)
                    except Exception:
                        pass
                    raise RuntimeError(f"Miro API error fetching items ({items_res.status_code}): {err_msg}")
                
                payload = items_res.json()
                data = payload.get("data", [])
                items.extend(data)
                cursor = payload.get("cursor")
                if not cursor or len(data) == 0:
                    break
                page += 1

            # 3. Fetch Connectors
            connectors: List[Dict[str, Any]] = []
            conn_res = await client.get(
                f"{self.api_base}/boards/{clean_id}/connectors",
                headers=headers,
                params={"limit": 50}
            )
            if conn_res.status_code == 200:
                conn_payload = conn_res.json()
                connectors = conn_payload.get("data", [])
            else:
                logger.warning(f"Miro connectors fetch returned {conn_res.status_code}: {conn_res.text}")

        return items, connectors, board_info

    async def fetch_board_graph(
        self,
        board_id: str,
        access_token: Optional[str] = None
    ) -> Tuple[NormalizedGraph, str, int, int]:
        """
        Fetches live board items, calculates board hash, and parses into a NormalizedGraph.
        Returns: (NormalizedGraph, board_hash, items_count, connectors_count)
        """
        items, connectors, board_info = await self.fetch_board_raw(board_id, access_token)
        board_hash = self.compute_board_hash(items, connectors)

        if not items:
            empty_graph = NormalizedGraph(
                nodes=[],
                edges=[],
                entry_node_id="",
                exit_node_ids=[]
            )
            return empty_graph, board_hash, 0, len(connectors)

        board_title = board_info.get("name") if board_info else "Miro Whiteboard"
        normalized_graph = miro_parser.parse_board_payload(items, connectors, board_title=board_title)
        return normalized_graph, board_hash, len(items), len(connectors)

    async def sync_and_compile(
        self,
        board_id: str,
        access_token: Optional[str] = None,
        force_recompile: bool = False
    ) -> Tuple[ExecutableAgentSpec, str, int, int]:
        """
        Synchronizes live Miro board and compiles into an ExecutableAgentSpec via Qwen.
        Caches compilation by board hash to prevent redundant LLM invocations.
        """
        graph, board_hash, items_cnt, conns_cnt = await self.fetch_board_graph(board_id, access_token)
        
        if items_cnt == 0:
            empty_spec = ExecutableAgentSpec(
                agent_name="Empty Miro Whiteboard",
                description="No nodes detected on this Miro board. Add sticky notes or cards tagged with [INPUT], [DECISION], [TOOL], [LLM], [OUTPUT] to begin.",
                entry_point="",
                nodes=[],
                edges=[]
            )
            return empty_spec, board_hash, 0, conns_cnt

        if not force_recompile and board_hash in self._compiled_cache:
            return self._compiled_cache[board_hash], board_hash, items_cnt, conns_cnt

        compiled_spec = await qwen_compiler.compile(graph)
        self._compiled_cache[board_hash] = compiled_spec
        return compiled_spec, board_hash, items_cnt, conns_cnt

    async def watch_board_stream(
        self,
        board_id: str,
        access_token: Optional[str] = None,
        poll_interval_sec: float = 2.5
    ) -> AsyncGenerator[str, None]:
        """
        Server-Sent Events (SSE) generator.
        Continuously polls Miro board for changes and yields 'board_synced' events
        whenever items, connectors, positions, or text are modified in Miro.
        """
        last_hash: Optional[str] = None
        heartbeat_counter = 0

        while True:
            try:
                token = self._resolve_token(access_token)
                if not token:
                    yield f"event: auth_required\ndata: {json.dumps({'message': 'Miro Access Token is required for live sync.'})}\n\n"
                    await asyncio.sleep(4.0)
                    continue

                clean_id = self._resolve_board_id(board_id)
                items, connectors, board_info = await self.fetch_board_raw(clean_id, token)
                current_hash = self.compute_board_hash(items, connectors)

                if len(items) == 0:
                    if last_hash != "empty":
                        last_hash = "empty"
                        yield f"event: board_empty\ndata: {json.dumps({'board_id': clean_id, 'message': 'Miro board connected, but canvas contains no items yet.'})}\n\n"
                elif current_hash != last_hash:
                    board_title = board_info.get("name") if board_info else "Miro Whiteboard"
                    graph = miro_parser.parse_board_payload(items, connectors, board_title=board_title)
                    spec = await qwen_compiler.compile(graph)
                    self._compiled_cache[current_hash] = spec
                    last_hash = current_hash

                    payload = {
                        "event_type": "board_synced",
                        "board_id": clean_id,
                        "board_title": board_info.get("name") if board_info else "Miro Whiteboard",
                        "board_hash": current_hash,
                        "items_count": len(items),
                        "connectors_count": len(connectors),
                        "spec": spec.model_dump(),
                    }
                    yield f"event: board_synced\ndata: {json.dumps(payload)}\n\n"
                else:
                    heartbeat_counter += 1
                    if heartbeat_counter >= 3:
                        heartbeat_counter = 0
                        yield f"event: heartbeat\ndata: {json.dumps({'board_id': clean_id, 'status': 'synced', 'hash': current_hash[:8]})}\n\n"

            except PermissionError as pe:
                yield f"event: auth_error\ndata: {json.dumps({'error': str(pe)})}\n\n"
                await asyncio.sleep(5.0)
            except FileNotFoundError as fe:
                yield f"event: not_found\ndata: {json.dumps({'error': str(fe)})}\n\n"
                await asyncio.sleep(5.0)
            except Exception as e:
                logger.error(f"Live sync poll error: {e}")
                yield f"event: sync_error\ndata: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(4.0)

            await asyncio.sleep(poll_interval_sec)

    async def write_audit_sticky_note(
        self,
        board_id: str,
        content: str,
        x: float = 300.0,
        y: float = 100.0,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a real red warning sticky note directly on the live Miro canvas.
        """
        token = self._resolve_token(access_token)
        if not token:
            raise ValueError("Miro Access Token is required to write back to the Miro board.")

        clean_id = self._resolve_board_id(board_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        body = {
            "data": {
                "content": f"<p>⚠️ <strong>[BoardMorph Audit]</strong><br/>{content}</p>"
            },
            "position": {"x": x, "y": y},
            "style": {"fillColor": "red"}
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{self.api_base}/boards/{clean_id}/sticky_notes",
                headers=headers,
                json=body
            )
            if res.status_code in [200, 201]:
                return {"status": "created", "note": res.json()}
            else:
                raise RuntimeError(f"Miro API error ({res.status_code}): {res.text}")

    async def write_fix_node(
        self,
        board_id: str,
        title: str,
        x: float = 400.0,
        y: float = 200.0,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a real green guardrail shape directly onto the live Miro whiteboard.
        """
        token = self._resolve_token(access_token)
        if not token:
            raise ValueError("Miro Access Token is required to write back to the Miro board.")

        clean_id = self._resolve_board_id(board_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        body = {
            "data": {
                "content": f"<p><strong>[TOOL] {title}</strong><br/>Resilient fallback layer</p>",
                "shape": "round_rectangle"
            },
            "position": {"x": x, "y": y},
            "geometry": {"width": 240, "height": 100},
            "style": {"fillColor": "light_green"}
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{self.api_base}/boards/{clean_id}/shapes",
                headers=headers,
                json=body
            )
            if res.status_code in [200, 201]:
                return {"status": "created", "shape": res.json()}
            else:
                raise RuntimeError(f"Miro API error ({res.status_code}): {res.text}")

# Global singleton
miro_sync_service = MiroSyncService()
miro_service = miro_sync_service
