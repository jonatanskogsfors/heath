import datetime


def pretty_duration(duration: datetime.timedelta, round_seconds: bool = False):
    if duration is None:
        return ""

    if round_seconds:
        total_seconds = round(duration.total_seconds() / 60) * 60
    else:
        total_seconds = duration.total_seconds()

    hours, rest = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(rest, 60)

    return f"{hours}:{minutes:02}" + (f":{seconds:02}" if seconds else "")


def pretty_time(time: datetime.time | datetime.datetime, italic=False):
    return time.strftime("%-H:%M") if time is not None else ""


def pretty_days(days: int) -> str:
    return f"{days}"


def time_to_seconds(time: datetime.time | datetime.datetime):
    return time.hour * 3600 + time.minute * 60 + time.second
