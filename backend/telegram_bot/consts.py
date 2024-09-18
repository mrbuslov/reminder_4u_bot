from aiogram import types

AVAILABLE_CONTENT_TYPES = [types.ContentType.TEXT, types.ContentType.VOICE]
PRETTY_DATE_FORMAT = "%A, %B %d, %Y"  # Monday, June 03, 2024
PRETTY_DATE_FORMAT_SHORT = "%d.%m"  # 03.09
PRETTY_TIME_FORMAT = "%H:%M"  # 14:34
PRETTY_DATE_TIME_FORMAT_SHORT = "%A, %B %d at %H:%M"  # Monday, June 03 at 14:34
PRETTY_DATE_TIME_FORMAT = "%A, %B %d, %Y at %H:%M"  # Monday, June 03, 2024 at 14:34
PATTERN_EXTRACT_UTC_FROM_LOCATION = r"[+-]\d{2}:\d{2}"

SYSTEM_MESSAGES = {
    "start_command": "Hello! Send me the <b>voice</b> or <b>text</b> message to create or delete the reminder",
    "help_command": """
Hello {user_name}! I'm the AI Reminder bot. 🤖\n
You send me your free-form text OR voice reminders, and I'll make sure you never forget them!\n
Send me the voice message!

<b>What you can do:</b>
- Send voice and text messages to <b>create</b> OR <b>delete</b> reminders.
For example: "set a reminder in 5 minutes to do something" OR "delete the reminder to visit the doctor for tomorrow at 8 am"
- Set your location and change the language the bot can talk to you (see below).

<b>Commands that you can use:</b>
/help - get information about the bot and its capabilities
/set_location - set your location for correct defining of your timezone
/set_language - set your language
/list - list reminders for today
/list_all - list all reminders
    """,
    "location_command": "<b>Country</b>. Send me your <b>country</b> or <b>city</b> in which you live to set the correct timezone",
    "location_changed": "Timezone is updated to {region_n_timezone}!",
    "location_not_changed": "I can't get timezone from your location. Please try again with city or country.",
    "language_command": "<b>Language</b>. Send me the <b>language</b> you want to receive messages from the bot",
    "language_changed": "Language is updated to {language}!",
    "language_not_changed": "I can't get language from your message. Please try again.",
    "message_voice_processing": "I received your voice message. Processing the reminder...",
    "message_text_processing": "I received your text message. Processing the reminder...",
    "message_any": "Sorry, we don't accept such type of messages. Please, send a <u>voice</u> or <u>text</u> message",
    "list_command_invalid": "You don't have any reminders for today",
    "list_all_command_invalid": "You don't have any reminders at all",
}
