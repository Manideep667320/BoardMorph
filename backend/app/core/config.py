import os
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "BoardMorph"
    API_PREFIX: str = "/api"
    
    # Qwen / LLM settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    QWEN_API_KEY: str = os.getenv(
        "QWEN_API_KEY", 
        os.getenv("OPENROUTER_API_KEY", os.getenv("DASHSCOPE_API_KEY", os.getenv("OPENAI_API_KEY", "")))
    )
    QWEN_BASE_URL: str = os.getenv(
        "QWEN_BASE_URL",
        "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    QWEN_MODEL: str = os.getenv(
        "QWEN_MODEL",
        "qwen/qwen-2.5-72b-instruct" if (os.getenv("OPENROUTER_API_KEY") or "openrouter" in os.getenv("QWEN_BASE_URL", "")) else "qwen-plus"
    )
    USE_MOCK_LLM_FALLBACK: bool = True  # Fallback to smart simulated compiler if API key unavailable
    
    # Custom headers for OpenRouter attribution
    LLM_HEADERS: dict = {
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "BoardMorph"
    }
    
    # Miro App settings (Direct REST API)
    MIRO_ACCESS_TOKEN: str = os.getenv("MIRO_ACCESS_TOKEN", "")
    MIRO_CLIENT_ID: str = os.getenv("MIRO_CLIENT_ID", "")
    MIRO_CLIENT_SECRET: str = os.getenv("MIRO_CLIENT_SECRET", "")
    MIRO_BOARD_ID: str = os.getenv("MIRO_BOARD_ID", "")
    MIRO_API_BASE_URL: str = "https://api.miro.com/v2"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"]
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @model_validator(mode="after")
    def sync_credentials(self) -> "Settings":
        if self.OPENROUTER_API_KEY:
            if not self.QWEN_API_KEY:
                self.QWEN_API_KEY = self.OPENROUTER_API_KEY
            if not self.QWEN_BASE_URL or "dashscope" in self.QWEN_BASE_URL:
                self.QWEN_BASE_URL = "https://openrouter.ai/api/v1"
            if not self.QWEN_MODEL or self.QWEN_MODEL == "qwen-plus":
                self.QWEN_MODEL = "qwen/qwen-2.5-72b-instruct"
        return self

settings = Settings()
