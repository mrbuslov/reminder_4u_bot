import asyncio
import functools


def get_running_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        print("A new event loop was spawned.")
        asyncio.set_event_loop(loop)
    return loop
