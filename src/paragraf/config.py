"""Central settings. Every value can be overridden with a PARAGRAF_* environment variable or a .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PARAGRAF_", env_file=".env")

    database_url: str = "postgresql://paragraf:paragraf@localhost:5432/paragraf"
    embed_model: str = "BAAI/bge-m3"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    device: str = "mps"                      # "cpu" inside Docker
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:7b"
    llm_api_key: str = "ollama"              # Ollama ignores it; hosted APIs need a real key
    anthropic_api_key: str = ""              # only for the optional hosted judge in eval/ (set it in .env)
    candidates: int = 30                     # size of the hybrid candidate list
    top_k: int = 5                           # sources sent to the LLM after reranking


settings = Settings()
