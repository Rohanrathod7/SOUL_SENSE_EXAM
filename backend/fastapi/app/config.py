from pydantic_settings import BaseSettings, SettingsConfigDict
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
DATA_DIR = ROOT_DIR / "data"
SQLITE_DB_PATH = DATA_DIR / "soulsense.db"

# Ensure the project root is on sys.path and the data directory exists
sys.path.insert(0, str(ROOT_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    welcome_message: str = "Welcome to Soul Sense!"

    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Database settings
    database_type: str = "sqlite"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "soulsense"
    db_user: str = "postgres"
    db_password: str = "password"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="SOULSENSE_",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.database_type == "postgresql":
            return (
                f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:"
                f"{self.db_port}/{self.db_name}"
            )
        return f"sqlite:///{SQLITE_DB_PATH}"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
