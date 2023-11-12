import datetime

import pytest

from heath import time_utils


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
            time_utils.pretty_duration(given_duration, round_seconds=True)
            == expected_string
    )
