from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base de datos
    db_server: str
    db_database: str = "DW_GrupoTDM"
    db_username: str
    db_password: str
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_port: int = 1433
    db_trust_server_certificate: bool = True

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # API
    api_title: str = "DW GrupoTDM API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_hosts: str = "*"
    environment: str = "development"
    enable_export: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def connection_string(self) -> str:
        trust_cert = "yes" if self.db_trust_server_certificate else "no"
        return (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={self.db_server},{self.db_port};"
            f"DATABASE={self.db_database};"
            f"UID={self.db_username};"
            f"PWD={self.db_password};"
            f"TrustServerCertificate={trust_cert};"
        )

settings = Settings()
