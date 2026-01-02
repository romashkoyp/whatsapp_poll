from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytz
import requests
from requests import Response

# Load environment variables from .env file for local development
# This is a no-op in GitHub Actions where env vars are set directly
try:
    from dotenv import load_dotenv
    # Look for .env file in the same directory as this script
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("📁 Loaded environment variables from .env file")
except ImportError:
    # python-dotenv not installed, rely on system environment variables
    pass

# Environment variables for sensitive configuration
# These should be set via GitHub Secrets or local .env file
GREENAPI_URL = os.environ.get("GREENAPI_URL", "")
GREENAPI_INSTANCE_ID = os.environ.get("GREENAPI_INSTANCE_ID", "")
GREENAPI_API_TOKEN = os.environ.get("GREENAPI_API_TOKEN", "")
CHAT_ID = os.environ.get("WHATSAPP_CHAT_ID", "")
FORCE_RUN = os.environ.get("FORCE_RUN", "false").lower() == "true"

# Construct API URL from components
API_URL = (
    f"{GREENAPI_URL}/waInstance{GREENAPI_INSTANCE_ID}/sendPoll/{GREENAPI_API_TOKEN}"
)

FIRST_OPTION = "Kyllä"
SECOND_OPTION = "Ei"
REQUEST_TIMEOUT = 10  # seconds


def get_current_day_finnish_time() -> str:
    finnish_tz = pytz.timezone("Europe/Helsinki")
    return datetime.now(finnish_tz).strftime("%A").lower()


def get_message_for_day(day: str) -> Optional[str]:
    if day == "friday":
        return "Tänään vääntämään klo 18:00? (test message)"
    if day == "saturday":
        return "Tänään vääntämään klo 12:00? (test message)" 
    return None


def build_payload(message: str) -> Dict[str, Any]:
    # Keep payload construction isolated for easier testing/extension.
    return {
        "chatId": CHAT_ID,
        "message": message,
        "multipleAnswers": False,
        "options": [
            {"optionName": FIRST_OPTION},
            {"optionName": SECOND_OPTION},
        ],
    }


def send_poll(url: str, payload: Dict[str, Any]) -> Response:
    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response


def validate_environment() -> bool:
    """Validate that all required environment variables are set."""
    required_vars = {
        "GREENAPI_INSTANCE_ID": GREENAPI_INSTANCE_ID,
        "GREENAPI_API_TOKEN": GREENAPI_API_TOKEN,
        "WHATSAPP_CHAT_ID": CHAT_ID,
    }

    missing = [name for name, value in required_vars.items() if not value]

    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("Please set these variables in GitHub Secrets or your environment.")
        return False

    return True


def main() -> None:
    print(f"🕐 Current Finnish time: {datetime.now(pytz.timezone('Europe/Helsinki'))}")

    if not validate_environment():
        sys.exit(1)

    current_day = get_current_day_finnish_time()
    print(f"📅 Current day: {current_day}")

    message = get_message_for_day(current_day)

    if not message:
        if FORCE_RUN:
            print("⚠️ Force run enabled, but no message configured for today.")
        else:
            print(f"ℹ️ No poll scheduled for {current_day}. Exiting.")
        return

    print(f"📨 Preparing to send poll: {message}")

    payload = build_payload(message)
    try:
        response = send_poll(API_URL, payload)
        print(f"✅ Poll sent successfully!")
        print(f"📄 Response: {response.text}")
    except requests.RequestException as exc:
        print(f"❌ Failed to send poll: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()