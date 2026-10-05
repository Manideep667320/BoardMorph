from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.agent import router as agent_router
from backend.app.api.execution import router as execution_router
from backend.app.api.miro import router as miro_router

app = FastAPI(
    title=settings.APP_NAME,
    description="BoardMorph: Visual Agent Builder (Miro x Qwen)",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(agent_router, prefix=settings.API_PREFIX)
app.include_router(execution_router, prefix=settings.API_PREFIX)
app.include_router(miro_router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "qwen_configured": bool(settings.QWEN_API_KEY),
        "miro_configured": bool(settings.MIRO_ACCESS_TOKEN)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
