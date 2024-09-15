#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from huey import RedisHuey

from core import settings

# Apply monkey-patch if we are running the huey consumer.
if "run_huey" in sys.argv:
    from gevent import monkey

    monkey.patch_all()

HUEY_CONFIG = settings.HUEY
huey_instance = RedisHuey(
    name=HUEY_CONFIG["name"],
    host=HUEY_CONFIG["connection"]["host"],
    port=HUEY_CONFIG["connection"]["port"],
    db=HUEY_CONFIG["connection"]["db"],
    results=HUEY_CONFIG["results"],
    store_none=HUEY_CONFIG["store_none"],
    immediate=HUEY_CONFIG["immediate"],
    utc=HUEY_CONFIG["utc"],
    blocking=HUEY_CONFIG["blocking"],
    connection_pool=HUEY_CONFIG["connection"]["connection_pool"],
    read_timeout=HUEY_CONFIG["connection"]["read_timeout"],
    url=HUEY_CONFIG["connection"]["url"],
)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
