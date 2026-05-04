"""Minimal configuration — path management and essential settings.

After the opencode-first redesign, fu7ur3pr00f defers LLM provider selection
and model orchestration to opencode. This module handles only filesystem paths
and a few essential constants.
"""

import os
from pathlib import Path

from .utils.security import secure_mkdir


class PathManager:
    """Manages application directory paths under ~/.fu7ur3pr00f/."""

    @property
    def data_dir(self) -> Path:
        return Path.home() / ".fu7ur3pr00f"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "data" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "data" / "processed"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "data" / "output"

    @property
    def market_cache_dir(self) -> Path:
        return self.data_dir / "data" / "market_cache"

    def ensure_directories(self) -> None:
        secure_mkdir(self.data_dir)
        for d in [self.raw_dir, self.processed_dir, self.output_dir, self.market_cache_dir]:
            secure_mkdir(d)


class Settings(PathManager):
    """Minimal settings — paths plus a few env-driven constants."""

    knowledge_chunk_max_tokens: int = int(os.getenv("KNOWLEDGE_CHUNK_MAX_TOKENS", "500"))
    knowledge_chunk_min_tokens: int = int(os.getenv("KNOWLEDGE_CHUNK_MIN_TOKENS", "50"))
    knowledge_auto_index: bool = os.getenv("KNOWLEDGE_AUTO_INDEX", "1") == "1"

    # Embedding provider: "openai", "azure", "ollama", or "" (local fallback)
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    azure_embedding_deployment: str = os.getenv(
        "AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
    )
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    fu7ur3pr00f_proxy_key: str = os.getenv("FUTUREPROOF_PROXY_KEY", "")
    fu7ur3pr00f_proxy_url: str = os.getenv("FUTUREPROOF_PROXY_URL", "https://llm.fu7ur3pr00f.dev")

    @property
    def active_provider(self) -> str:
        if self.embedding_provider:
            return self.embedding_provider
        if self.azure_openai_api_key and self.azure_openai_endpoint:
            return "azure"
        if self.openai_api_key:
            return "openai"
        if self.fu7ur3pr00f_proxy_key:
            return "fu7ur3pr00f"
        if self.ollama_base_url:
            return "ollama"
        return ""


settings = Settings()
