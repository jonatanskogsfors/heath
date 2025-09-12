import datetime
import re

from heath.exceptions import TimeError

TIME_PATTERN = re.compile(r"(2[0-3])|([0-1]?[0-9])(:[0-5][0-9](:[0-5][0-9])?)?")


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


def parse_time(time_string: str) -> datetime.time:
    if not TIME_PATTERN.fullmatch(time_string):
        raise TimeError(f"Could not parse time string '{time_string}'.")
    return datetime.time(*(int(number) for number in time_string.split(":")))


def parse_duration(duration_string: str) -> datetime.timedelta:
    if not TIME_PATTERN.fullmatch(duration_string):
        raise TimeError(f"Could not parse duration string '{duration_string}'.")

    return datetime.timedelta(
        **dict(
            zip(
                ("hours", "minutes", "seconds"),
                (int(number) for number in duration_string.split(":")),
            )
        )
    )
