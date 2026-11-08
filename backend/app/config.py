from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always locate backend/.env reliably regardless of where python is executed
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE), ".env"),
        extra="ignore",
    )

    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    database_url: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    classifier_model: str = "openai/gpt-oss-120b"
    agent_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"
    gcp_project_id: str = ""
    pubsub_topic: str = ""
    webhook_url: str = ""
    dashboard_username: str = "admin"
    dashboard_password: str = ""


settings = Settings()
