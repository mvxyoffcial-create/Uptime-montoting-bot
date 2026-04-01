class temp:
    """Shared in-memory state."""
    B_LINK = "https://t.me/mvxyoffcail"   # bot/promo link shown in logs


async def get_seconds(time_str: str) -> int:
    """
    Convert a human-readable time string to seconds.

    Supported formats (case-insensitive):
        "1 day", "2 days"
        "1 hour", "3 hours"
        "30 min", "30 mins", "30 minute", "30 minutes"
        "1 month", "2 months"
        "1 year", "2 years"

    Returns 0 if the format is invalid.
    """
    try:
        parts = time_str.strip().lower().split()
        if len(parts) != 2:
            return 0

        value = int(parts[0])
        unit = parts[1].rstrip("s")  # normalise plural → singular

        mapping = {
            "second":  1,
            "minute":  60,
            "min":     60,
            "hour":    3600,
            "day":     86400,
            "week":    604800,
            "month":   2592000,   # 30 days
            "year":    31536000,  # 365 days
        }

        return value * mapping.get(unit, 0)
    except (ValueError, KeyError):
        return 0
