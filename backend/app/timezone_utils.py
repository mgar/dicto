"""Helpers for converting between user-local dates and UTC-naive storage."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _zoneinfo_from_name(time_zone: str | None):
    if not time_zone:
        return None
    try:
        return ZoneInfo(time_zone)
    except ZoneInfoNotFoundError:
        return None


def timezone_from_request(tz_offset: int | None = None, time_zone: str | None = None):
    user_tz = _zoneinfo_from_name(time_zone)
    if user_tz:
        return user_tz

    offset_minutes = -(tz_offset or 0)
    return timezone(timedelta(minutes=offset_minutes))


def local_date_from_utc(
    utc_dt: datetime,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> date:
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(timezone_from_request(tz_offset, time_zone)).date()


def local_datetime_to_utc_naive(
    local_day: date,
    local_time: time,
    tz_offset: int | None = None,
    time_zone: str | None = None,
) -> datetime:
    local_dt = datetime.combine(
        local_day,
        local_time,
        tzinfo=timezone_from_request(tz_offset, time_zone),
    )
    return local_dt.astimezone(timezone.utc).replace(tzinfo=None)
