"""Clock helpers for Traffix simulation runtime."""

from datetime import datetime
from zoneinfo import ZoneInfo

WIB_TIMEZONE = ZoneInfo("Asia/Jakarta")


def get_current_wib_time() -> str:
    """Return the current time formatted in Western Indonesia Time.

    Returns:
        Current Asia/Jakarta time formatted with WIB suffix.
    """
    return datetime.now(WIB_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S WIB")
