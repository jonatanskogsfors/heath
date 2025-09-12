import datetime

import pytest

from heath import time_utils
from heath.exceptions import TimeError


@pytest.mark.parametrize(
    "given_duration, expected_string",
    (
        (None, ""),
        (datetime.timedelta(), "0:00"),
        (datetime.timedelta(seconds=1), "0:00:01"),
        (datetime.timedelta(seconds=59), "0:00:59"),
        (datetime.timedelta(seconds=90), "0:01:30"),
        (datetime.timedelta(minutes=1), "0:01"),
        (datetime.timedelta(minutes=59), "0:59"),
        (datetime.timedelta(minutes=90), "1:30"),
        (datetime.timedelta(minutes=13, seconds=37), "0:13:37"),
        (datetime.timedelta(hours=1), "1:00"),
        (datetime.timedelta(hours=23), "23:00"),
        (datetime.timedelta(hours=100), "100:00"),
        (datetime.timedelta(hours=1, minutes=1), "1:01"),
        (datetime.timedelta(hours=1, minutes=1, seconds=1), "1:01:01"),
        (datetime.timedelta(hours=13, minutes=33, seconds=37), "13:33:37"),
        (datetime.timedelta(days=1), "24:00"),
        (datetime.timedelta(days=2, hours=2, minutes=25, seconds=12), "50:25:12"),
        (datetime.timedelta(days=1, seconds=1), "24:00:01"),
    ),
)
def test_pretty_duration(given_duration: datetime.timedelta, expected_string: str):
    assert time_utils.pretty_duration(given_duration) == expected_string


@pytest.mark.parametrize(
    "given_time, expected_string",
    (
        (None, ""),
        (datetime.time(), "0:00"),
        (datetime.time(1), "1:00"),
        (datetime.time(23), "23:00"),
        (datetime.time(0, 1), "0:01"),
        (datetime.time(0, 1, 59, 9999), "0:01"),
        (datetime.time(13, 37), "13:37"),
    ),
)
def test_pretty_time(given_time: datetime.time, expected_string: str):
    assert time_utils.pretty_time(given_time) == expected_string


@pytest.mark.parametrize(
    "given_duration, expected_string",
    (
        (None, ""),
        (datetime.timedelta(), "0:00"),
        (datetime.timedelta(seconds=1), "0:00"),
        (datetime.timedelta(seconds=59), "0:01"),
        (datetime.timedelta(seconds=90), "0:02"),
        (datetime.timedelta(minutes=13, seconds=37), "0:14"),
        (datetime.timedelta(hours=1, minutes=1, seconds=1), "1:01"),
        (datetime.timedelta(hours=13, minutes=33, seconds=37), "13:34"),
        (datetime.timedelta(hours=1, minutes=59, seconds=31), "2:00"),
        (datetime.timedelta(hours=1, minutes=59, seconds=30), "2:00"),
        (datetime.timedelta(hours=1, minutes=59, seconds=29), "1:59"),
        (datetime.timedelta(hours=23, minutes=59, seconds=31), "24:00"),
    ),
)
def test_pretty_duration_with_rounding(
    given_duration: datetime.timedelta, expected_string: str
):
    assert (
        time_utils.pretty_duration(given_duration, round_seconds=True) == expected_string
    )


@pytest.mark.parametrize(
    "given_time_string, expected_time",
    (
        ("0:00", datetime.time(0)),
        ("00:00", datetime.time(0)),
        ("1:23", datetime.time(1, 23)),
        ("01:23", datetime.time(1, 23)),
        ("01:23:45", datetime.time(1, 23, 45)),
        ("8", datetime.time(8)),
    ),
)
def test_parse_time(given_time_string, expected_time):
    # When parsing user input string
    parsed_time = time_utils.parse_time(given_time_string)

    # Then the correct time is created
    assert parsed_time == expected_time


@pytest.mark.parametrize(
    "given_time_string",
    (
        "",
        "000:00",  # Too many leading zeros
        "1:23:45:67",  # Beyond second precision
        "24:00",
        "12:60",
        "12:34:60",
        "8:50am",
        "0_05",  # Real world case that was accepted
    ),
)
def test_parse_time_rejects_bad_time_strings(given_time_string):
    with pytest.raises(TimeError):
        time_utils.parse_time(given_time_string)


@pytest.mark.parametrize(
    "given_duration_string, expected_timedelta",
    (
        ("0:00", datetime.timedelta()),
        ("00:00", datetime.timedelta()),
        ("1:23", datetime.timedelta(hours=1, minutes=23)),
        ("01:23", datetime.timedelta(hours=1, minutes=23)),
        ("01:23:45", datetime.timedelta(hours=1, minutes=23, seconds=45)),
        ("8", datetime.timedelta(hours=8)),
    ),
)
def test_parse_duration(given_duration_string, expected_timedelta):
    # When parsing user input string
    parsed_time = time_utils.parse_duration(given_duration_string)

    # Then the correct time is created
    assert parsed_time == expected_timedelta


@pytest.mark.parametrize(
    "given_duration_string",
    (
        "",
        "000:00",  # Too many leading zeros
        "1:23:45:67",  # Beyond second precision
        "24:00",
        "12:60",
        "12:34:60",
        "8:50am",
        "0_05",  # Real world case that was accepted
    ),
)
def test_parse_duration_rejects_bad_duration_strings(given_duration_string):
    with pytest.raises(TimeError):
        time_utils.parse_time(given_duration_string)
