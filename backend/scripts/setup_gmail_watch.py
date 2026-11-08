import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import db
from app.config import settings
from app.gmail import Gmail


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_gmail_watch")


def main() -> None:
    if not settings.pubsub_topic:
        logger.error("PUBSUB_TOPIC not configured in environment or .env")
        sys.exit(1)

    gmail = Gmail()
    logger.info("Setting up Gmail watch for topic: %s", settings.pubsub_topic)
    res = gmail.setup_watch(topic_name=settings.pubsub_topic)
    history_id = res.get("historyId")
    expiration = res.get("expiration")
    logger.info("Watch response: historyId=%s, expiration=%s", history_id, expiration)

    if history_id and expiration:
        db.upsert_watch_state(history_id, expiration)
        logger.info("Successfully persisted watch state to database!")


if __name__ == "__main__":
    main()

