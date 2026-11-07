from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env into the environment, so Pydantic AI also finds API_KEY.
load_dotenv()


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    database_url: str
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