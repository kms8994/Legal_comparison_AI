from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    database_url: str | None = None
    law_open_api_oc: str | None = None
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_structure_model: str = "gemini-2.5-flash-lite"
    llm_query_model: str = "gemini-2.5-flash-lite"
    embedding_provider: str = "gemini"
    embedding_model: str = "gemini-embedding-001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
