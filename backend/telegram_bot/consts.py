from aiogram import types

AVAILABLE_CONTENT_TYPES = [types.ContentType.TEXT, types.ContentType.VOICE]
PRETTY_DATE_FORMAT = "%A, %B %d, %Y"  # Monday, June 03, 2024
PRETTY_DATE_TIME_FORMAT = (
    "%A, %B %d, %Y at %I:%M %p"  # Monday, June 03, 2024 at 02:34 PM
)

SYSTEM_MESSAGES = {
    "start_command": """
Hello {user_name}! I'm the AI Reminder bot. 🤖\n
You send me your free-form text OR voice reminders, and I'll make sure you never forget them!\n
Just drop your reminders here, and I'll handle the rest. Give it a try!
    """,
    "help_command": """
Hello {user_name}! I'm the AI Reminder bot. 🤖\n
You send me your free-form text OR voice reminders, and I'll make sure you never forget them!\n
Just drop your reminders here, and I'll handle the rest. Give it a try!

<b>What you can do:</b>
- Send voice and text messages to <b>set</b> OR <b>delete</b> reminders.
For example: "set a reminder in 5 minutes to do something" OR "delete the reminder to visit the doctor for tomorrow at 8 am"
- Set your location and change the language the bot can talk to you (see below).

<b>Commands that you can use:</b>
/help - get information about the bot and its capabilities
/set_location - set your location for correct defining of your timezone
/set_language - set your language
/list - list reminders for today
/list_all - list all reminders
    """,
    "location_command": "Please send me your location",
    "location_changed": "Timezone is updated to {region_n_timezone}!",
    "location_not_changed": "I can't get timezone from your location. Please try again with city or country",
    "language_command": "Please send me in which language you feel comfortable receiving messages from the bot",
    "language_changed": "Language is updated to {language}!",
    "language_not_changed": "I can't get language from your message. Please try again",
    "message_voice_processing": "I received your voice message. Processing the reminder...",
    "message_text_processing": "I received your text message. Processing the reminder...",
    "message_any": "Sorry, we don't accept such type of messages. Please, send a <u>voice</u> or <u>text</u> message",
    "list_command_invalid": "You don't have any reminders for today",
    "list_all_command_invalid": "You don't have any reminders at all",
}
