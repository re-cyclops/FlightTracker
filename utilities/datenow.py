"""centralized date/time helper with optional DEBUG_DATE/DEBUG_TIME overrides."""
import sys
from datetime import datetime


def get_now():
    """get current datetime, with optional date/time overrides from config.

    if DEBUG_DATE is set in config (format: "MM-DD"), returns a datetime
    with that month/day but real hours/minutes/seconds. this allows
    testing holiday animations without changing the system clock.

    if DEBUG_TIME is set in config (format: "HH:MM"), overrides the
    hour/minute the same way (seconds stay real) for testing quiet hours.
    """
    now = datetime.now()

    try:
        from config import DEBUG_DATE
    except (ImportError, NameError):
        DEBUG_DATE = None

    if DEBUG_DATE:
        try:
            month, day = map(int, DEBUG_DATE.split("-"))
            now = now.replace(month=month, day=day)
        except (ValueError, AttributeError):
            print(f"[WARNING] invalid DEBUG_DATE '{DEBUG_DATE}', using real date", file=sys.stderr)

    try:
        from config import DEBUG_TIME
    except (ImportError, NameError):
        DEBUG_TIME = None

    if DEBUG_TIME:
        try:
            hour, minute = map(int, DEBUG_TIME.split(":"))
            now = now.replace(hour=hour, minute=minute)
        except (ValueError, AttributeError):
            print(f"[WARNING] invalid DEBUG_TIME '{DEBUG_TIME}', using real time", file=sys.stderr)

    return now
