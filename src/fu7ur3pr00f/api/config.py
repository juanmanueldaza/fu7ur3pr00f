from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class APISettings(BaseSettings):
    """API configuration settings populated via environment variables."""
    
    host: str = Field(default="127.0.0.1", description="Host binding address")
    port: int = Field(default=8000, description="Port binding mapping")
    reload: bool = Field(default=False, description="Enable or disable hot-reloading")
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins list")
    chroma_dir: str = Field(default="fu7ur3pr00f/src/fu7ur3pr00f/memory/chromadb_store.py")
    profile_path: str = Field(default="fu7ur3pr00f/src/fu7ur3pr00f/memory/profile.py")
    log_level: str = Field(default="INFO", description="Application logger severity level")

    model_config = SettingsConfigDict(env_prefix="FP_", case_sensitive=False)

settings = APISettings()