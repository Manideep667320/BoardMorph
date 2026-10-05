"""
Compatibility stub: Miro MCP integration has been migrated to direct Miro REST API app integration.
Import from backend.app.services.miro_service instead.
"""
from backend.app.services.miro_service import (
    MiroSyncService,
    miro_sync_service,
    miro_service
)

miro_mcp_service = miro_sync_service
