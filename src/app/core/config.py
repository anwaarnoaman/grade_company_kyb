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

    # Azure storage
    azure_storage_blob_connection_string: str = ""
    azure_storage_container: str = "documents"

    database_url: str = ""
    database_url_async :str=""
    # Pydantic config to load .env locally
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

def get_keyvault_client() -> SecretClient | None:
    """Return a Key Vault client if KEY-VAULT-URL is set, else None."""
    key_vault_url = os.environ.get("KEY-VAULT-URL")
    if not key_vault_url:
        return None
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=key_vault_url, credential=credential)

def load_settings() -> Settings:
    kv_client = get_keyvault_client()

    if kv_client:
        # Fetch secrets from Azure Key Vault in production
        secret_key = kv_client.get_secret("SECRET-KEY").value
        algorithm = kv_client.get_secret("ALGORITHM").value
        app_name = kv_client.get_secret("APP-NAME").value

        # Fetch Azure Storage secrets 
        azure_storage_blob_connection_string = kv_client.get_secret(
                "AZURE-STORAGE-BLOB-CONNECTION-STRING"
            ).value

        return Settings(
                secret_key=secret_key,
                algorithm=algorithm,
                app_name=app_name,
                azure_storage_blob_connection_string=azure_storage_blob_connection_string,
                debug=os.environ.get("DEBUG", "False").lower() == "true"
            )
    else:
        # Local development: Pydantic will automatically load from .env
        return Settings()

# Global settings instance
settings = load_settings()