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
SANITY_SCHEDULE_URL = os.environ.get("SANITY_SCHEDULE_URL", "")

# Construct API URL from components
API_URL_POLL = (
    f"{GREENAPI_URL}/waInstance{GREENAPI_INSTANCE_ID}/sendPoll/{GREENAPI_API_TOKEN}"
)

API_URL_MESSAGE = (
    f"{GREENAPI_URL}/waInstance{GREENAPI_INSTANCE_ID}/sendMessage/{GREENAPI_API_TOKEN}" 
)

POSITIVE_ANSWER = "Kyllä"
NEGATIVE_ANSWER = "Ei"
CANCEL_TEXT = "Huom, tänään treeni peruttu!"
EXCEPTION_TEXT = "Tänään poikkeukselliset treenit."
STANDARD_TEXT= "Tänään vääntämään klo"
MESSAGE_ERROR = "❌ Invalid schedule data structure"
REQUEST_TIMEOUT = 10  # seconds
USE_SAMPLE_RESPONSE = False  # Set to True to use sample response data for testing

# Sample response data
SAMPLE_RESPONSE = {
    "query": "*[_type == \"allDays\"]",
    "result": [{
        "_createdAt": "2026-01-06T10:43:55Z",
        "_id": "7437c1ac-ec4b-4083-8702-fd341a810c36",
        "_type": "allDays",
        "_updatedAt": "2026-01-06T13:45:26Z",
        "canceledDays": [
            {"_key": "819b95f4119e", "_type": "canceledDay", "date": "2026-07-01"},
            {"_key": "42a76733805e", "_type": "canceledDay", "date": "2025-08-11"},
            {"_key": "658c41af5aca", "_type": "canceledDay", "date": "2025-09-23"},
            {"_key": "953b0a74a43c", "_type": "canceledDay", "date": "2025-12-23"}
        ],
        "exceptionDays": [
            {"_key": "a02e3811bc1f", "_type": "exceptionDay", "date": "2026-07-01", "endTime": "20:00", "startTime": "18:00"},
            {"_key": "a042ac7b82ee", "_type": "exceptionDay", "date": "2025-08-12", "endTime": "20:00", "startTime": "18:00"},
            {"_key": "8f41321d0606", "_type": "exceptionDay", "date": "2025-09-22", "endTime": "20:00", "startTime": "18:00"},
            {"_key": "f4e1dff0840b", "_type": "exceptionDay", "date": "2025-12-22", "endTime": "20:00", "startTime": "18:00"}
        ],
        "title": "Arm Fight JKL ry - All Training Days",
        "trainingDays": [
            {"_key": "868a629380e9", "_type": "trainingDay", "endTime": "20:00", "startTime": "18:00", "weekDay": {"_type": "weekDay", "en": "Tuesday", "fi": "Tiistai", "key": "tuesday", "ru": "Вторник"}},
            {"_key": "a0d933b309cd", "_type": "trainingDay", "endTime": "14:00", "startTime": "12:00", "weekDay": {"_type": "weekDay", "en": "Saturday", "fi": "Lauantai", "key": "saturday", "ru": "Суbbota"}}
        ]
    }],
    "syncTags": ["s1:xXDwZQ"],
    "ms": 2
}


def get_current_date() -> str:
    """Get current date in Finnish time zone (YYYY-MM-DD)."""
    finnish_tz = pytz.timezone("Europe/Helsinki")
    return datetime.now(finnish_tz).strftime("%Y-%m-%d")


def get_current_day_of_week() -> str:
    """Get day of week in Finnish time zone."""
    finnish_tz = pytz.timezone("Europe/Helsinki")
    return datetime.now(finnish_tz).strftime("%A").lower()


def get_schedule_data() -> Optional[Dict[str, Any]]:
    """Fetch training schedule data from Sanity."""
    try:
        response = requests.get(SANITY_SCHEDULE_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"❌ Failed to fetch schedule from Sanity: {exc}")
        return None


def get_message_for_current_day(
        data: Dict[str, Any],
        current_date: str,
        day_of_week: str
    ) -> Optional[str]:
    """Get the message for the current day based on schedule from Sanity."""
    # Validate data structure
    if 'result' not in data or not data['result']:
        return MESSAGE_ERROR
    
    all_days = data['result'][0]
    training_days = all_days['trainingDays']
    canceled_days = all_days['canceledDays']
    exception_days = all_days['exceptionDays']

    if current_date in [d['date'] for d in canceled_days]:
        return API_URL_MESSAGE, CANCEL_TEXT

    if current_date in [d['date'] for d in exception_days]:
        exception = next(d for d in exception_days if d['date'] == current_date)
        start_time = exception['startTime']
        poll_message = f"{EXCEPTION_TEXT} {STANDARD_TEXT} {start_time}?"
        return API_URL_POLL, poll_message

    if any(td['weekDay']['key'] == day_of_week for td in training_days):
        training_day = next(td for td in training_days if td['weekDay']['key'] == day_of_week)
        start_time = training_day['startTime']
        poll_message = f"{STANDARD_TEXT} {start_time}?"
        return API_URL_POLL, poll_message

    return None


def build_payload(message: str) -> Dict[str, Any]:
    if message == None:
        return None
    
    if message == CANCEL_TEXT:
        return {
            "chatId": CHAT_ID,
            "message": message,
        }
    
    return {
        "chatId": CHAT_ID,
        "message": message,
        "multipleAnswers": False,
        "options": [
            {"optionName": POSITIVE_ANSWER},
            {"optionName": NEGATIVE_ANSWER},
        ],
    }


def send_message(url: str, payload: Dict[str, Any]) -> Response:
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
        "SANITY_SCHEDULE_URL": SANITY_SCHEDULE_URL,
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

    current_date = get_current_date()
    current_day = get_current_day_of_week()

    print(f"📅 Current date: {current_date}")
    print(f"📅 Current day of week: {current_day}")

    if USE_SAMPLE_RESPONSE:
        schedule_data = SAMPLE_RESPONSE
    else:
        schedule_data = get_schedule_data()

    if schedule_data is None:
        sys.exit(1)

    result = get_message_for_current_day(schedule_data, current_date, current_day)
    if result is None:
        print("ℹ️ No training scheduled for today. Exiting.")
        sys.exit(0)
    url, message = result

    if message == MESSAGE_ERROR:
        print(f"{MESSAGE_ERROR}")
        sys.exit(1)

    print(f"📨 Preparing to send message: {message}")

    try:
        payload = build_payload(message)
        response = send_message(url, payload)
        print("✅ Message sent successfully")
        print(f"📄 Response: {response.text}")
    except requests.RequestException as exc:
        resp = getattr(exc, "response", None)
        if resp is not None:
            print(f"❌ Failed to send poll: {resp.status_code} {resp.reason}")
            print(f"📄 Error body: {resp.text}")
        else:
            print(f"❌ Failed to send poll: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()