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
    evaluator_model: str = "openai/gpt-oss-120b"
    agent_model: str = "gemini-2.5-flash"
    agent_model01: str = ""
    agent_model02: str = ""
    agent_model03: str = ""
    agent_model04: str = ""
    embedding_model: str = "models/gemini-embedding-001"
    gcp_project_id: str = ""
    pubsub_topic: str = ""
    webhook_url: str = ""
    dashboard_username: str = "admin"
    dashboard_password: str = ""

    def get_agent_models(self) -> list[str]:
        """Return the prioritized list of models for the agent (primary + fallback models)."""
        models: list[str] = []

        # Check explicit sequential models (agent_model01, agent_model02, ...)
        for val in [
            self.agent_model01,
            self.agent_model02,
            self.agent_model03,
            self.agent_model04,
        ]:
            if val and val.strip() and val.strip() not in models:
                models.append(val.strip())

        # Check agent_model (supports single model or comma-separated list)
        if self.agent_model and self.agent_model.strip():
            for m in self.agent_model.split(","):
                m_clean = m.strip()
                if m_clean and m_clean not in models:
                    models.append(m_clean)

        # Fallback default if none provided
        if not models:
            models = ["gemini-2.5-flash"]

        return models


settings = Settings()
