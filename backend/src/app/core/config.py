from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General app settings
    app_name: str = "MyLocalApp"
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/app.log"
    temp_file_path: str = "temp"

    # Security / secrets
    secret_key: str
    algorithm: str

    # Azure storage
    azure_storage_blob_connection_string: str
    azure_storage_container: str

    # Database URLs
    database_url: str
    database_url_async: str

    # Load from .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unknown env vars
    )


# Global settings instance
settings = Settings()