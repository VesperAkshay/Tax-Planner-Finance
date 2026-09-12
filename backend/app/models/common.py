from datetime import datetime as dt_datetime, timezone as dt_timezone


def get_utc_now() -> dt_datetime:
    """Returns an offset-naive UTC datetime suitable for PostgreSQL TIMESTAMP WITHOUT TIME ZONE."""
    return dt_datetime.now(dt_timezone.utc).replace(tzinfo=None)
