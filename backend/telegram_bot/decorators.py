import asyncio
import functools

from core.settings import telegram_bot_logger


def get_running_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        telegram_bot_logger.info("A new event loop was spawned.")
        asyncio.set_event_loop(loop)
    return loop
