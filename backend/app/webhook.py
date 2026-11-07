import base64
import json
import logging
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app import db
from app.config import settings
from app.gmail import Gmail
from app.pipeline import handle_message

logger = logging.getLogger(__name__)

router = APIRouter()


def process_history_changes(history_id: int | str) -> None:
    """Fetch new messages since last known history_id and process them."""
    gmail = Gmail()
    last_state = db.get_watch_state()
    start_history_id = (
        last_state["history_id"] if last_state and last_state.get("history_id") else history_id
    )

    logger.info("Checking history changes starting from historyId: %s", start_history_id)
    try:
        new_ids = gmail.list_history(start_history_id)
    except Exception as e:
        logger.error("Failed to list history: %s. Falling back to list_new_message_ids.", e)
        new_ids = gmail.list_new_message_ids(max_results=5)

    # If history is valid, update current history_id
    if history_id:
        expiration = (
            last_state.get("expiration")
            if last_state
            else int(time.time() * 1000) + (7 * 86400 * 1000)
        )
        db.upsert_watch_state(history_id=history_id, expiration=expiration)

    logger.info("Found %d new message(s) from history sync: %s", len(new_ids), new_ids)
    for msg_id in new_ids:
        try:
            handle_message(gmail, msg_id)
        except Exception:
            logger.exception("Error handling message %s in webhook task", msg_id)


@router.post("/webhook/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks) -> dict:
    """
    Endpoint for Google Cloud Pub/Sub push subscription.
    Acknowledges immediately with HTTP 200 and processes events in background.
    """
    body = await request.json()
    if not body or "message" not in body:
        logger.warning("Invalid Pub/Sub push payload received")
        return {"status": "ignored", "reason": "no message field"}

    pubsub_msg = body.get("message", {})
    data_b64 = pubsub_msg.get("data", "")
    if not data_b64:
        return {"status": "ok", "detail": "empty data"}

    try:
        data_json = base64.b64decode(data_b64).decode("utf-8")
        payload = json.loads(data_json)
    except Exception as e:
        logger.error("Failed to decode Pub/Sub data payload: %s", e)
        return {"status": "error", "detail": "invalid base64 or json payload"}

    email_address = payload.get("emailAddress", "")
    history_id = payload.get("historyId")

    logger.info("Received Gmail push notification for %s, historyId: %s", email_address, history_id)

    if history_id:
        background_tasks.add_task(process_history_changes, history_id)

    return {"status": "ok"}

