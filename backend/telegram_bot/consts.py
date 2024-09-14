from aiogram import types

AVAILABLE_CONTENT_TYPES = [types.ContentType.TEXT, types.ContentType.VOICE]

SYSTEM_MESSAGES = {
    "start_command": """
Hello {user_name}! I'm the AI Reminder bot. 🤖\n
You send me your free-form text OR voice reminders, and I'll make sure you never forget them!\n
Just drop your reminders here, and I'll handle the rest. Give it a try!
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
}
