import datetime


def pretty_duration(delta: datetime.timedelta):
    if delta is None:
        return ""
    hours, rest = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02}" + (f":{seconds:02}" if seconds else "")


def pretty_time(time: datetime.time, italic=False):
    return time.strftime("%-H:%M") if time is not None else ""
