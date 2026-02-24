from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = ""
    debug: bool = False

    log_level: str = ""
    log_to_file: bool = False
    log_file_path: str = ""
    temp_file_path: str = "" 
   
    secret_key: str = ""
    algorithm: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
