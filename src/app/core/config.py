from pydantic_settings import BaseSettings, SettingsConfigDict
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

class Settings(BaseSettings):
    # General app settings
    app_name: str = "MyLocalApp"
    debug: bool = False

    # Logging
    log_level: str = ""
    log_to_file: bool = False
    log_file_path: str = ""
    temp_file_path: str = "" 

    # Security / secrets
    secret_key: str = "dev-secret-key"
    algorithm: str = "HS256"

    # Pydantic config to load .env locally
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

def get_keyvault_client() -> SecretClient | None:
    """Return a Key Vault client if KEY_VAULT_URL is set, else None."""
    key_vault_url = os.environ.get("KEY_VAULT_URL")
    if not key_vault_url:
        return None
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=key_vault_url, credential=credential)

def load_settings() -> Settings:
    kv_client = get_keyvault_client()

    if kv_client:
        # Fetch secrets from Azure Key Vault in production
        secret_key = kv_client.get_secret("SECRET_KEY").value
        algorithm = kv_client.get_secret("ALGORITHM").value
        app_name = kv_client.get_secret("APP_NAME").value

        return Settings(
            secret_key=secret_key,
            algorithm=algorithm,
            app_name=app_name,
            debug=os.environ.get("DEBUG", "False") == "True"  # prod default False
        )
    else:
        # Local development: Pydantic will automatically load from .env
        return Settings()

# Global settings instance
settings = load_settings()