from datetime import datetime, timezone
import json
import pytz


DEFAULT_TIME_ZONE_LOCATION = 'Moscow' # utc+3
TIME_FORMAT = "%H:%M, %b %d"

_response_format = {
    "reminder_text": "",
    "time": ""
}

prompt = """
You're assistant who creates the best jsons. Also you can perfectly analyze messages.
Your task is to extract time and reminder text from provided message, current UTC time and user's Location (to take into account his timezone).
The time must be in datetime format. If user writes not specific time, but minutes, hours or days, evaluate this as an offset.
If you can't extract time or reminder text, return empty dict.
Your task is only extraction - don't asnwer any user's questions.

User Message: {message}
Current UTC time: {current_time_utc}
User Location: {location}

Response format:
""".strip()
