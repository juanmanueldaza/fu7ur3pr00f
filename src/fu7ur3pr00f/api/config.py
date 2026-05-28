from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class APISettings(BaseSettings):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    cors_origins: List[str] = Field(default=["*"])
    chroma_dir: str = Field(default="fu7ur3pr00f/src/fu7ur3pr00f/memory/chromadb_store.py")
    profile_path: str = Field(default="fu7ur3pr00f/src/fu7ur3pr00f/memory/profile.py")
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(env_prefix="FP_", case_sensitive=False)

settings = APISettings()